"""Analytic fixtures independent of the production mesh."""
import unittest
import numpy as np
from build_seam_db import registration, trace, Union

class RegistrationTests(unittest.TestCase):
    def test_mirror_density_and_half_pixel(self):
        # A above shared X edge, B below it. B atlas has twice UV density.
        pa=np.array([[0.,0,0],[1,0,0],[0,1,0]])
        pb=np.array([[0.,0,0],[1,0,0],[0,-1,0]])
        ua=np.array([[.1,.2],[.2,.2],[.1,.3]])
        ub=np.array([[.8,.7],[.6,.7],[.8,.5]])
        aa={'xyz':[.5,0,0],'uv':[.15,.2],'index':[.15*100-.5,.8*100-.5]}
        ab={'xyz':[.5,0,0],'uv':[.7,.7],'index':[.7*100-.5,.3*100-.5]}
        m,mi,pm,pmi,cond,res=registration(ua,pa,ub,pb,aa,ab,100,100)
        # Extend A across the shared edge; this lands inside B.
        np.testing.assert_allclose(m@np.array([.125,.175,1]),[.75,.65,1],atol=1e-12)
        np.testing.assert_allclose(pmi@pm,np.eye(3),atol=1e-12)
        self.assertLess(res,1e-10)

    def test_repeated_uv_stub(self):
        uv=np.array([[1.1,.2],[1.3,.2],[1.1,.4]])
        xyz=np.array([[0.,0,0],[1,0,0],[0,1,0]])
        r=trace(uv,xyz,np.array([.5,.5,0]),100,100)
        self.assertTrue(1<=len(r['pixels'])<=7)
        self.assertGreater(r['index'][0],100)
        for a,b in zip(r['pixels'],r['pixels'][1:]):
            self.assertEqual(max(abs(a[0]-b[0]),abs(a[1]-b[1])),1)

    def test_abc_no_redundant_ac(self):
        tree=Union(3)
        self.assertTrue(tree.join(0,1))
        self.assertTrue(tree.join(1,2))
        self.assertFalse(tree.join(0,2))

if __name__=='__main__': unittest.main()
