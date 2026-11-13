#!/usr/bin/env python3
"""Offline pair diagnostics and masked native-detail PNG composition.

Requires numpy, Pillow and opencv-python. Does not acquire imagery or perform
global bundle optimization. Transforms map native source coordinates to base output.
"""
import argparse
import json
import math
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, PngImagePlugin

Image.MAX_IMAGE_PIXELS = None


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def load(path):
    # imdecode/fromfile also supports Unicode paths on Windows.
    im = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if im is None:
        raise ValueError(f'Cannot decode image: {path}')
    return im


def features(im, crop, exclusions=()):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    x0, y0, x1, y1 = crop or [0, 0, w, h]
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
        raise ValueError('Crop is outside the image')
    mask = np.zeros_like(gray)
    mask[y0:y1, x0:x1] = 255
    for a, b, c, d in exclusions:
        mask[max(0,b):min(h,d), max(0,a):min(w,c)] = 0
    factor = min(1., 1800 / max(h, w))
    if factor < 1:
        gray = cv2.resize(gray, None, fx=factor, fy=factor)
        mask = cv2.resize(mask, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_NEAREST)
    k, d = cv2.SIFT_create(nfeatures=16000).detectAndCompute(gray, mask)
    if d is None:
        raise ValueError('No distinctive features')
    return np.float32([p.pt for p in k]) / factor, d


def pair(args):
    pa, da = features(load(args.a), args.crop_a)
    pb, db = features(load(args.b), args.crop_b)
    matches = [m for pair in cv2.BFMatcher().knnMatch(db, da, k=2)
               if len(pair)==2 for m,n in [pair] if m.distance < .72 * n.distance]
    if len(matches) < 12:
        raise ValueError('Too few feature matches')
    b = np.float32([pb[m.queryIdx] for m in matches])
    a = np.float32([pa[m.trainIdx] for m in matches])
    H, mask = cv2.findHomography(b, a, cv2.RANSAC, 2.5)
    if H is None or mask.sum() < 12:
        raise ValueError('No reliable geometric match')
    keep = mask.ravel().astype(bool)
    a, b = a[keep], b[keep]
    predicted = cv2.perspectiveTransform(b[:, None], H)[:, 0]
    errors = np.linalg.norm(predicted - a, axis=1)
    shift = np.rint(np.median(a - b, axis=0)).astype(int)
    te = np.linalg.norm((b + shift) - a, axis=1)
    affine, _ = cv2.estimateAffinePartial2D(b, a, method=cv2.RANSAC)
    result = {
        'a': str(Path(args.a).resolve()), 'b': str(Path(args.b).resolve()),
        'H_b_to_a': H.tolist(), 'inliers': len(a),
        'median_projective_error_px': float(np.median(errors)),
        'p95_projective_error_px': float(np.percentile(errors, 95)),
        'integer_translation_b_to_a': shift.tolist(),
        'p95_translation_error_px': float(np.percentile(te, 95)),
        'translation_compatible': bool(np.percentile(te, 95) <= args.tolerance),
        'source_b_support_bbox': [*b.min(0).tolist(), *b.max(0).tolist()],
    }
    if affine is not None:
        result['similarity_scale_b_to_a'] = float(np.hypot(affine[0, 0], affine[1, 0]))
        result['similarity_rotation_degrees'] = float(np.degrees(np.arctan2(affine[1, 0], affine[0, 0])))
    dump(args.report, result)
    print(json.dumps(result))


def projected(H, points):
    return cv2.perspectiveTransform(np.float64(points)[None], H)[0]


def align(args):
    """Initial multi-image alignment; loop errors gate publication of a scene."""
    path = Path(args.manifest).resolve()
    manifest = json.loads(path.read_text(encoding='utf-8-sig'))
    sources = manifest['sources']
    if len(sources) < 2:
        raise ValueError('Alignment needs at least two overlapping images')
    paths = [(path.parent / s['file']).resolve() for s in sources]
    dims, fs = [], []
    for file, source in zip(paths, sources):
        im = load(file)
        dims.append((im.shape[1], im.shape[0]))
        fs.append(features(im, source.get('crop'), source.get('exclude', [])))
    trials, edges = set(), []

    def try_pair(i, j):
        if (i,j) in trials:
            return
        trials.add((i,j))
        pa, da = fs[i]; pb, db = fs[j]
        matches = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=64)).knnMatch(db, da, k=2)
        matches = [m for pair in matches if len(pair)==2 for m,n in [pair] if m.distance < .72*n.distance]
        if len(matches) < 15:
            return
        a = np.float32([pa[m.trainIdx] for m in matches])
        b = np.float32([pb[m.queryIdx] for m in matches])
        H, mask = cv2.findHomography(b, a, cv2.RANSAC, 2.5)
        if H is None or mask.sum() < 15:
            return
        keep = mask.ravel().astype(bool); a, b = a[keep], b[keep]
        if args.mode == 'translation':
            delta = np.rint(np.median(a-b, axis=0))
            if np.percentile(np.linalg.norm(a-b-delta,axis=1),95) > args.tolerance:
                return
            H = np.eye(3); H[:2,2] = delta
        # Reject unstable projective extrapolation and implausible camera flips.
        w,h = dims[j]
        footprint = projected(H, [[0,0],[w,0],[w,h],[0,h]])
        if not np.isfinite(footprint).all() or not cv2.isContourConvex(footprint.astype('float32')):
            return
        area = cv2.contourArea(footprint.astype('float32'), oriented=True)
        if not .2*w*h < area < 5*w*h:
            return
        step = max(1, len(a)//200)
        edges.append(dict(i=i,j=j,H=H,a=a[::step],b=b[::step],inliers=len(a)))

    for i in range(len(sources)):
        for j in range(i+1,len(sources)):
            row_neighbour = False
            if all(k in sources[i] and k in sources[j] for k in ['row','column']):
                row_neighbour = abs(sources[i]['row']-sources[j]['row'])<=1 and abs(sources[i]['column']-sources[j]['column'])<=1
            if args.all_pairs or j-i <= args.match_window or row_neighbour:
                try_pair(i,j)

    poses = {0:np.eye(3)}
    while len(poses)<len(sources):
        candidates=[e for e in edges if (e['i'] in poses)!=(e['j'] in poses)]
        if not candidates:
            dump(args.report, {'status':'disconnected','located_sources':sorted(poses),'source_count':len(sources)})
            raise ValueError('Disconnected capture graph: supply order/row metadata, try --all-pairs, or capture missing overlap')
        e=max(candidates,key=lambda e:e['inliers']);i,j=e['i'],e['j']
        if i in poses: poses[j]=poses[i]@e['H']
        else: poses[i]=poses[j]@np.linalg.inv(e['H'])

    if args.mode == 'translation':
        # Use loops as well as the spanning tree to reduce integer-shift drift.
        A=[];D=[]
        for e in edges:
            row=np.zeros(len(sources)-1)
            if e['j']:row[e['j']-1]+=1
            if e['i']:row[e['i']-1]-=1
            weight=math.sqrt(min(300,e['inliers']))
            A.append(row*weight);D.append(e['H'][:2,2]*weight)
        shifts=np.vstack([np.zeros((1,2)),np.rint(np.linalg.lstsq(A,D,rcond=None)[0])])
        for i in poses:poses[i]=np.eye(3);poses[i][:2,2]=shifts[i]

    errors=[]
    for e in edges:
        errors.extend(np.linalg.norm(projected(poses[e['i']],e['a'])-projected(poses[e['j']],e['b']),axis=1).tolist())
    p95=float(np.percentile(errors,95))
    report={'status':'aligned' if p95<=args.tolerance else 'needs_global_refinement',
            'sources':len(sources),'overlap_pairs':len(edges),'median_error_first_image_pixels':float(np.median(errors)),
            'p95_error_first_image_pixels':p95,'solver':'loop-fitted translations' if args.mode=='translation' else 'maximum-support spanning tree with loop checks'}
    dump(args.report,report)
    if p95 > args.tolerance:
        raise ValueError('Loop error too large; refine global transforms before rendering')
    footprints=[]
    for i,(w,h) in enumerate(dims):
        x0,y0,x1,y1=sources[i].get('crop',[0,0,w,h])
        footprints.extend(projected(poses[i],[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]))
    footprints=np.array(footprints)
    lo=np.floor(footprints.min(0));hi=np.ceil(footprints.max(0))
    T=np.array([[1,0,-lo[0]],[0,1,-lo[1]],[0,0,1.]])
    scene={'width':int(hi[0]-lo[0]),'height':int(hi[1]-lo[1]),'margin':0 if args.mode=='translation' else 4,
           'source':manifest.get('source','Map screenshot mosaic'),'extent_review_required':True,'sources':[]}
    for i,source in enumerate(sources):
        scene['sources'].append({**source,'file':str(paths[i]),'H':(T@poses[i]).tolist()})
    dump(args.scene,scene)
    print(json.dumps(report))


@contextmanager
def mapped_buffers(folder, height, width):
    buffers = []
    try:
        for name, dtype, shape in [
            ('rgb', 'uint8', (height, width, 3)),
            ('score', 'uint16', (height, width)),
            ('owner', 'uint16', (height, width)),
        ]:
            buffers.append(np.memmap(folder / name, mode='w+', dtype=dtype, shape=shape))
        yield tuple(buffers)
    finally:
        # Explicit closure is needed before TemporaryDirectory cleanup on Windows,
        # including validation failures; deleting one array reference is insufficient.
        for buffer in buffers:
            try:
                buffer.flush()
            except (OSError, ValueError):
                pass  # Temporary work buffers still need closing on failure.
            finally:
                buffer._mmap.close()


def render(args):
    scene_path = Path(args.scene).resolve()
    scene = json.loads(scene_path.read_text(encoding='utf-8-sig'))
    sources = scene['sources']
    if not 0 < len(sources) < 65535:
        raise ValueError('Expected 1..65534 explicitly listed sources')
    base_w, base_h = int(scene['width']), int(scene['height'])
    if min(base_w, base_h) <= 0:
        raise ValueError('Invalid output dimensions')
    required = 1.
    prepared = []
    for source in sources:
        path = (scene_path.parent / source['file']).resolve()
        with Image.open(path) as image:
            w, h = image.size
        crop = source.get('crop', [0, 0, w, h])
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ValueError(f'Invalid crop: {path}')
        H = np.asarray(source['H'], dtype=float)
        if H.shape != (3, 3) or not np.isfinite(H).all() or abs(np.linalg.det(H)) < 1e-12:
            raise ValueError(f'Invalid homography: {path}')
        if abs(H[2, 2]) < 1e-12:
            raise ValueError('Homography cannot be normalized safely')
        H /= H[2, 2]
        if args.mode == 'translation':
            want = np.eye(3)
            want[:2, 2] = np.rint(H[:2, 2])
            if not np.allclose(H, want, atol=1e-9, rtol=0):
                raise ValueError('Strict mode permits integer translation only')
        signs = []
        for y in np.linspace(y0, y1, 3):
            for x in np.linspace(x0, x1, 3):
                q = H @ [x, y, 1.]
                signs.append(q[2])
                if abs(q[2]) < 1e-9:
                    raise ValueError('Projection singularity')
                u, v = q[:2] / q[2]
                J = (H[:2, :2] - np.outer([u, v], H[2, :2])) / q[2]
                if np.linalg.det(J) <= 0:
                    raise ValueError('Folded or reflected projection')
                required = max(required, 1 / np.linalg.svd(J)[1].min())
        if min(signs) < 0 < max(signs):
            raise ValueError('Projection crosses infinity')
        prepared.append((path, H, crop, source.get('exclude', [])))
    scale = 1 if args.mode == 'translation' else math.ceil(required - 1e-9)
    W, HH = base_w * scale, base_h * scale
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output.parent).free < W * HH * 13:
        raise ValueError('Insufficient free workspace for native-resolution buffers and PNG')
    quality = {'width': W, 'height': HH, 'sources': len(sources), 'mode': args.mode,
               'output_scale': scale, 'sampled_required_scale': required}
    with tempfile.TemporaryDirectory(prefix='mosaic-', dir=output.parent) as temp:
        temp = Path(temp)
        with mapped_buffers(temp, HH, W) as (rgb, scores, owner):
            for index, (path, H, crop, exclusions) in enumerate(prepared, 1):
                x0, y0, x1, y1 = crop
                cw, ch = x1 - x0, y1 - y0
                yy, xx = np.ogrid[:ch, :cw]
                weight = (np.minimum(np.minimum(xx, cw-1-xx), np.minimum(yy, ch-1-yy)) + 1).astype('float32')
                margin = int(scene.get('margin', 4))
                if margin < 0 or margin * 2 >= min(cw, ch):
                    raise ValueError('Invalid interpolation margin')
                if margin:
                    weight[:margin] = weight[-margin:] = 0
                    weight[:, :margin] = weight[:, -margin:] = 0
                for ex0, ey0, ex1, ey1 in exclusions:
                    pad = 3 if args.mode == 'projective' else 0
                    xa, xb = max(0, ex0-x0-pad), min(cw, ex1-x0+pad)
                    ya, yb = max(0, ey0-y0-pad), min(ch, ey1-y0+pad)
                    if xb > xa and yb > ya:
                        weight[ya:yb, xa:xb] = 0
                transform = np.diag([scale, scale, 1.]) @ H @ np.array([[1,0,x0],[0,1,y0],[0,0,1.]])
                corners = projected(transform, [[0,0],[cw,0],[cw,ch],[0,ch]])
                xa, ya = np.maximum(0, np.floor(corners.min(0)-2)).astype(int)
                xb, yb = np.minimum([W, HH], np.ceil(corners.max(0)+2)).astype(int)
                if xb <= xa or yb <= ya:
                    continue
                local = np.array([[1,0,-xa],[0,1,-ya],[0,0,1.]]) @ transform
                im = load(path)[y0:y1, x0:x1, ::-1].copy()
                flag = cv2.INTER_NEAREST if args.mode == 'translation' else cv2.INTER_CUBIC
                tile = cv2.warpPerspective(im, local, (xb-xa, yb-ya), flags=flag)
                # Nearest validity avoids interpolating excluded pixels into the map.
                valid = cv2.warpPerspective((weight > 0).astype('uint8'), local, (xb-xa, yb-ya), flags=cv2.INTER_NEAREST)
                ws = cv2.warpPerspective(weight, local, (xb-xa, yb-ya), flags=cv2.INTER_NEAREST).clip(0,65535).astype('uint16')
                ws[valid == 0] = 0
                sc = scores[ya:yb, xa:xb]
                take = ws > sc
                rgb[ya:yb, xa:xb][take] = tile[take]
                owner[ya:yb, xa:xb][take] = index
                sc[take] = ws[take]
            quality['uncovered_pixels'] = int(np.count_nonzero(owner == 0))
            quality['status'] = 'complete' if quality['uncovered_pixels'] == 0 else 'incomplete'
            dump(args.report, quality)
            if quality['uncovered_pixels']:
                raise ValueError(f"Uncovered output pixels: {quality['uncovered_pixels']}; capture replacements")
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text('Source', scene.get('source', 'Map screenshots; provider recorded by the caller'))
            metadata.add_text('Processing', json.dumps(quality))
            encoded = temp / 'encoded.png'
            Image.fromarray(np.asarray(rgb)).save(encoded, format='PNG', pnginfo=metadata, compress_level=6)
            with Image.open(encoded) as check:
                check.verify()
            encoded.replace(output)
            quality['bytes'] = output.stat().st_size
            quality['output'] = str(output)
            if args.ownership:
                Image.fromarray(np.asarray(owner)).save(args.ownership)
            if args.preview:
                im = Image.fromarray(np.asarray(rgb))
                im.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                im.save(args.preview)
            dump(args.report, quality)

    print(json.dumps(quality))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('pair')
    p.add_argument('a'); p.add_argument('b'); p.add_argument('--report', required=True)
    p.add_argument('--crop-a', nargs=4, type=int); p.add_argument('--crop-b', nargs=4, type=int)
    p.add_argument('--tolerance', type=float, default=2.)
    p.set_defaults(run=pair)
    p = commands.add_parser('align', help='Initial batch alignment; inspect extent and seams before rendering')
    p.add_argument('manifest'); p.add_argument('--scene', required=True); p.add_argument('--report', required=True)
    p.add_argument('--mode', choices=['translation','projective'], default='translation')
    p.add_argument('--match-window', type=int, default=3); p.add_argument('--all-pairs', action='store_true')
    p.add_argument('--tolerance', type=float, default=3.)
    p.set_defaults(run=align)
    p = commands.add_parser('render')
    p.add_argument('scene'); p.add_argument('--out', required=True); p.add_argument('--report', required=True)
    p.add_argument('--mode', choices=['translation','projective'], default='translation')
    p.add_argument('--preview'); p.add_argument('--ownership')
    p.set_defaults(run=render)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, KeyError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
