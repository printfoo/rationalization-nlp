cd raw
wget "https://s3-eu-west-1.amazonaws.com/pfigshare-u-files/7554634/attack_annotated_comments.tsv"
wget "https://s3-eu-west-1.amazonaws.com/pfigshare-u-files/7554637/attack_annotations.tsv"
wget "https://raw.githubusercontent.com/shcarton/rcnn/master/deliberativeness/data/processed/wiki/personal_attacks/wiki_attack_dev_rationale.csv"
wget "https://raw.githubusercontent.com/shcarton/rcnn/master/deliberativeness/data/processed/wiki/personal_attacks/wiki_attack_test_rationale.csv"
wget "https://raw.githubusercontent.com/uds-lsv/lexicon-of-abusive-words/master/Lexicons/baseLexicon.txt"
cd ..
python data_cleaner.py
python data_signaler.py

