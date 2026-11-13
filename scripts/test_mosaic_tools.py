"""Offline self-tests; no UI, network, credentials or map downloads."""
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image
import mosaic_tools as mt


class MosaicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stitch-maps-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Карта с пробелами'
        self.root.mkdir()
        self.original = np.random.default_rng(27).integers(0,256,(256,512,3),dtype=np.uint8)
        a = self.original[:,:332].copy(); a[100:130,200:230]=[255,0,0]
        Image.fromarray(a).save(self.root/'лево.png')
        Image.fromarray(self.original[:,180:]).save(self.root/'право.png')
        Image.fromarray(self.original[:,90:422]).save(self.root/'центр.png')
        self.scene={'width':512,'height':256,'margin':0,'sources':[
            {'file':'лево.png','exclude':[[200,100,230,130]],'H':[[1,0,0],[0,1,0],[0,0,1]]},
            {'file':'право.png','H':[[1,0,180],[0,1,0],[0,0,1]]}]}

    def write(self,name,value):
        path=self.root/name
        path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
        return path

    def call(self,*args,code=0):
        p=subprocess.run([sys.executable,str(Path(mt.__file__).resolve()),*map(str,args)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(p.returncode,code,p.stdout+'\n'+p.stderr)
        return p

    def test_pair_unicode_shift(self):
        self.call('pair',self.root/'лево.png',self.root/'право.png','--report',self.root/'pair.json')
        result=json.loads((self.root/'pair.json').read_text())
        self.assertTrue(result['translation_compatible'])
        self.assertEqual(result['integer_translation_b_to_a'],[180,0])

    def test_strict_pixels_and_cursor_mask(self):
        scene=self.write('scene.json',self.scene)
        self.call('render',scene,'--out',self.root/'map.png','--report',self.root/'quality.json','--ownership',self.root/'owner.png')
        with Image.open(self.root/'map.png') as image:
            np.testing.assert_array_equal(np.array(image),self.original)

    def test_utf8_bom_manifest_and_scene(self):
        path=self.root/'BOM.json'
        path.write_text(json.dumps(self.scene,ensure_ascii=False),encoding='utf-8-sig')
        self.call('render',path,'--out',self.root/'bom.png','--report',self.root/'bom-quality.json')
        manifest={'sources':[{'file':'лево.png','exclude':[[200,100,230,130]]},{'file':'право.png'}]}
        path.write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8-sig')
        self.call('align',path,'--scene',self.root/'bom-scene.json','--report',self.root/'bom-align.json')

    def test_projective_native_sampling_and_strict_rejection(self):
        scene=json.loads(json.dumps(self.scene));scene['width']=256;scene['height']=128
        for s in scene['sources']:
            s['H'][0]=[v*.5 for v in s['H'][0]];s['H'][1]=[v*.5 for v in s['H'][1]]
        path=self.write('scaled.json',scene)
        self.call('render',path,'--mode','projective','--out',self.root/'large.png','--report',self.root/'large.json')
        with Image.open(self.root/'large.png') as image:
            self.assertEqual(image.size,(512,256))
            np.testing.assert_array_equal(np.array(image),self.original)
        self.call('render',path,'--out',self.root/'rejected.png','--report',self.root/'rejected.json',code=2)
        scene['sources'][0]['H']=[[1.000001,0,0],[0,1,0],[0,0,1]]
        self.call('render',self.write('near.json',scene),'--out',self.root/'near.png','--report',self.root/'near-report.json',code=2)

    def test_batch_alignment(self):
        source=self.scene['sources'][0]
        manifest={'sources':[source,{'file':'центр.png'},{'file':'право.png'}]}
        self.call('align',self.write('inputs.json',manifest),'--scene',self.root/'aligned.json','--report',self.root/'align-report.json')
        self.call('render',self.root/'aligned.json','--out',self.root/'batch.png','--report',self.root/'batch-quality.json')
        with Image.open(self.root/'batch.png') as image:
            np.testing.assert_array_equal(np.array(image),self.original)

    def test_disconnected_batch(self):
        noise=np.random.default_rng(993).integers(0,256,(256,332,3),dtype=np.uint8)
        Image.fromarray(noise).save(self.root/'other.png')
        manifest={'sources':[{'file':'лево.png'},{'file':'other.png'}]}
        self.call('align',self.write('apart.json',manifest),'--scene',self.root/'apart-scene.json','--report',self.root/'apart-report.json',code=2)
        self.assertFalse((self.root/'apart-scene.json').exists())

    def test_scaled_capture_projective_alignment(self):
        Image.fromarray(self.original).save(self.root/'whole.png')
        warped=mt.cv2.warpAffine(self.original,np.float64([[1.05,0,-10],[0,1.05,-5]]),(512,256))
        Image.fromarray(warped).save(self.root/'scaled capture.png')
        self.call('pair',self.root/'whole.png',self.root/'scaled capture.png','--report',self.root/'scaled-pair.json')
        result=json.loads((self.root/'scaled-pair.json').read_text())
        self.assertFalse(result['translation_compatible'])
        q=mt.projected(np.array(result['H_b_to_a']),[[305,184]])[0]
        self.assertLess(np.linalg.norm(q-[300,180]),1.5)
        manifest={'sources':[{'file':'whole.png'},{'file':'scaled capture.png'}]}
        self.call('align',self.write('projective-inputs.json',manifest),'--mode','projective','--scene',self.root/'projective-scene.json','--report',self.root/'projective-report.json')
        self.assertEqual(json.loads((self.root/'projective-report.json').read_text())['status'],'aligned')

    def test_mappings_closed_on_success_and_failure(self):
        real=mt.np.memmap; tracked=[]
        def record(*args,**kwargs):
            value=real(*args,**kwargs);tracked.append(value);return value
        scene=self.write('mapped.json',self.scene)
        args=argparse.Namespace(scene=str(scene),out=str(self.root/'mapped.png'),report=str(self.root/'mapped-quality.json'),mode='translation',preview=None,ownership=None)
        with mock.patch.object(mt.np,'memmap',side_effect=record):
            mt.render(args)
        self.assertTrue(tracked and all(m._mmap.closed for m in tracked))
        tracked.clear();self.scene['sources'][1]['H'][0][2]=400
        self.write('mapped.json',self.scene)
        before=(self.root/'mapped.png').read_bytes()
        with mock.patch.object(mt.np,'memmap',side_effect=record):
            with self.assertRaises(ValueError):mt.render(args)
        self.assertTrue(tracked and all(m._mmap.closed for m in tracked))
        self.assertEqual((self.root/'mapped.png').read_bytes(),before)
        quality=json.loads((self.root/'mapped-quality.json').read_text())
        self.assertGreater(quality['uncovered_pixels'],0)
        self.assertFalse(list(self.root.glob('mosaic-*')))


if __name__=='__main__':unittest.main(verbosity=2)
