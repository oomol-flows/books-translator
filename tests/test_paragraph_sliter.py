import unittest
from shared.epub.paragraph_sliter import split_paragraph

class _Test(unittest.TestCase):

  def test_normal_english(self):
    self.assertEqual(
      split_paragraph("The reckoning by five does not amount to such a variation of the decimal system as that which was in use among the Celts and Danes. these peoples had a vigesimal system, traces of which are still left in the French quatre-vingts, quatre-vingt-treize, &c., and in our score, three-score and ten, twenty-one, &c."),
      [
        "The reckoning by five does not amount to such a variation of the decimal system as that which was in use among the Celts and Danes.",
        " these peoples had a vigesimal system, traces of which are still left in the French quatre-vingts, quatre-vingt-treize, &c., and in our score, three-score and ten, twenty-one, &c.",
      ],
    )

  def test_normal_chinese(self):
    self.assertEqual(
      split_paragraph("换言之，穷人的幸福（他的所有希望应说是很容易找到活儿干并不遭歉收之苦）迟早要从富人的繁荣中走出来，不是吗？当时任梅斯总督的年轻的卡洛纳说：“一般来说，雇农及短工与耕农的关系，就是辅助与主要的关系，当人们改善了耕农的命运时，就不必为雇农和短工的命运焦虑了；"),
      [
        "换言之，穷人的幸福（他的所有希望应说是很容易找到活儿干并不遭歉收之苦）迟早要从富人的繁荣中走出来，不是吗？",
        "当时任梅斯总督的年轻的卡洛纳说：“一般来说，雇农及短工与耕农的关系，就是辅助与主要的关系，当人们改善了耕农的命运时，就不必为雇农和短工的命运焦虑了；",
      ]
    )

  def test_bracket_english(self):
    self.assertEqual(
      split_paragraph("This use of the letters of the alphabet as numerals (it was original with the Greeks. they did not derive it from the Phoenicians). The earliest occurrence of numerals written in this way appears to be in a Halicarnassian inscription of date not long after 450 B.C."),
      [
        "This use of the letters of the alphabet as numerals (it was original with the Greeks. they did not derive it from the Phoenicians).",
        " The earliest occurrence of numerals written in this way appears to be in a Halicarnassian inscription of date not long after 450 B.C.",
      ],
    )

  def test_bracket_chinese(self):
    self.assertEqual(
      split_paragraph("除了以上所列的文献（此处以及上文第206页。见注1），还可参见同一篇记载的 \nfol. 400 v°\n（1432年12月5日，1438年8月6日证实），以及385（1439年12月29日）——在迪涅，高山牧场的公共放牧制也于1365年被禁止实行三年。"),
      [
        "除了以上所列的文献（此处以及上文第206页。见注1），还可参见同一篇记载的 \nfol. 400 v°\n（1432年12月5日，1438年8月6日证实），以及385（1439年12月29日）——在迪涅，高山牧场的公共放牧制也于1365年被禁止实行三年。",
      ],
    )

  def test_bugs(self):
    self.assertEqual(
      split_paragraph('<p class="indent"><span class="space">    </span>The interest of the subject for the classical scholar is no doubt of a different kind. Greek mathematics reveals an important aspect of the Greek genius of which the student of Greek culture is apt to lose sight. Most people, when they think of the Greek genius, naturally call to mind its masterpieces in literature and art with their notes of beauty, truth, freedom and humanism. But the Greek, with his insatiable desire to know the true meaning of everything in the universe and to be able to give a rational explanation of it, was just as irresistibly driven to natural science, mathematics, and exact reasoning in general or logic. This austere side of the Greek genius found perhaps its most complete expression in Aristotle. Aristotle would, however, by no means admit that mathematics was divorced from aesthetic; he could conceive, he said, of nothing more beautiful than the objects of mathematics. Plato delighted in geometry and in the wonders of numbers; <i>ἀγεωμέτρητος μηδεὶς εἰσίτω</i>, said the inscription over the door of the Academy. Euclid was a no less typical Greek. Indeed, seeing that so much of Greek is mathematics, <a id="page_vi"></a>it is arguable that, if one would understand the Greek genius fully, it would be a good plan to begin with their geometry.</p>'),
      [
        '<p class="indent"><span class="space">    </span>The interest of the subject for the classical scholar is no doubt of a different kind.',
        ' Greek mathematics reveals an important aspect of the Greek genius of which the student of Greek culture is apt to lose sight.',
        ' Most people, when they think of the Greek genius, naturally call to mind its masterpieces in literature and art with their notes of beauty, truth, freedom and humanism.',
        ' But the Greek, with his insatiable desire to know the true meaning of everything in the universe and to be able to give a rational explanation of it, was just as irresistibly driven to natural science, mathematics, and exact reasoning in general or logic.',
        ' This austere side of the Greek genius found perhaps its most complete expression in Aristotle.',
        ' Aristotle would, however, by no means admit that mathematics was divorced from aesthetic;', 
        ' he could conceive, he said, of nothing more beautiful than the objects of mathematics.',
        ' Plato delighted in geometry and in the wonders of numbers;',
        ' <i>ἀγεωμέτρητος μηδεὶς εἰσίτω</i>, said the inscription over the door of the Academy.',
        ' Euclid was a no less typical Greek.',
        ' Indeed, seeing that so much of Greek is mathematics, <a id="page_vi"></a>it is arguable that, if one would understand the Greek genius fully, it would be a good plan to begin with their geometry.</p>',
      ],
    )
    self.assertEqual(
      split_paragraph("The period from the late fourth to the late second century B.C."),
      ['The period from the late fourth to the late second century B.C.']
    )