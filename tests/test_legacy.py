import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import legacy,news
class LegacyReceipts(unittest.TestCase):
 def setUp(self):
  self.d=news.load(news.ROOT/'docs/data/daily/2026-09-27.json');self.item=copy.deepcopy(self.d['items'][0])
 def test_exact_same_day_receipt(self):self.assertTrue(legacy.admitted(self.item,self.d,news.ROOT))
 def test_receipt_cannot_relabel_old_event_as_new_day(self):
  d=copy.deepcopy(self.d);d['date']='2026-09-28';self.assertFalse(legacy.admitted(self.item,d,news.ROOT))
 def test_receipt_does_not_allow_changed_payload(self):
  self.item['summary']='An unverified different fact';self.assertFalse(legacy.admitted(self.item,self.d,news.ROOT))
 def test_receipt_does_not_permit_section_promotion(self):
  self.item['section']='radar';self.assertFalse(legacy.admitted(self.item,self.d,news.ROOT))
if __name__=='__main__':unittest.main()
