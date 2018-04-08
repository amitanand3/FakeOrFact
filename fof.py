from pattern.en import ngrams
from pattern.web import Google, SEARCH
from pattern.db import Datasheet
from pattern.db  import pd
from collections import defaultdict
import csv
import string
import collections
import re
import nltk
from nltk.corpus import stopwords
from nltk import ne_chunk, pos_tag
import sys
import json

class FoF(object):

	def __init__(self, text, language, max_queries = 10, span = 20, threshold = .8):
		self.max_queries = max_queries
		self.span = span
		self.threshold = threshold
		self.text = text
		self.language = language
		self.cat_dict = defaultdict(list)
		key = 'AIzaSyDZzslNRAsgyiiBKx36S8rblRKungcypEA'
		self.engine = Google(license=key, throttle=0.5, language=None)
		self.urls = []

	def reconstruct_ngram(self, ngram):
		punc_b = ['!', '?', '.', ',', ';', ':', '\'', ')', ']', '}']
		punc_a = ['(', '[', '}', '$']
		ngram = ' '.join(ngram)
		for p in punc_b:
			ngram = ngram.replace(' '+p, p)
		for p in punc_a:
			ngram = ngram.replace(p+' ', p)
		ngram = re.sub('(^| )BEGQ', ' "', ngram)
		ngram = re.sub('ENDQ($| )', '" ', ngram)
		ngram = ngram.replace('DOUBLEDASH', '--')
		return ngram 

	def get_queries(self):
		text = self.text
		beg_quotes = re.findall(r'\"\S', text)
		for each in beg_quotes:
			text = text.replace(each, 'BEGQ' + each[-1])

		end_quotes = re.findall(r'\S\"', text)
		for each in end_quotes:
			text = text.replace(each, each[0] + 'ENDQ')

		text = re.sub('(ENDQ)+', 'ENDQ', text)
		text = re.sub('(BEGQ)+', 'BEGQ', text)
		text = text.replace('--', 'DOUBLEDASH')

		all_ngrams = ngrams(text, n = self.span, punctuation = "", continuous = True)
		if self.language in stopwords.fileids():
			stop_words = stopwords.words(self.language)
		else:
			stop_words = []	
		queries = []
		for ngram in all_ngrams:
			num_stop = len([w for w in ngram if w in stop_words])
			stop_score = float(num_stop)/len(ngram)
			if self.language == 'english':
				chunked = ne_chunk(pos_tag(ngram))
				named_entities = [[w for w, t in elt] for elt in chunked if isinstance(elt, nltk.Tree)]
				num_ent = sum([len(ent_list) for ent_list in named_entities])
				ent_score = float(num_ent)/len(ngram)
			else:
				ent_score = 0

			if stop_score < self.threshold and ent_score < self.threshold:
				r_string = self.reconstruct_ngram(ngram)
				if r_string in self.text:
					queries.append(r_string)
		reduction = len(queries)/self.max_queries
		return queries[0::reduction]

	def get_domain(self, full_url):
		clean_reg= re.compile(r'^((?:https?:\/\/)?(?:www\.)?).*?(\/.*)?$')
		match = re.search(clean_reg, full_url)
		self.urls.append(full_url)
		beg, end = match.group(1), match.group(2)
		domain = string.replace(full_url, beg, '')
		domain = string.replace(domain, end, '')
		return domain

	def get_urls(self, queries):
		domains = defaultdict(list)
		for q in queries:
			q = "\"" + q + "\""
			results = self.engine.search(q)

			for result in results:			
				url = result.url
				domain = self.get_domain(url)
				domains[domain].append(q)
		return domains
	
	def load_domains(self):
		sources_path = pd('data', 'data.csv')
		domain_file = Datasheet.load(sources_path, headers = True)
		for row in domain_file:
			url  = row[1]
			cats = row[2:]
			self.cat_dict[url] = cats

	def render_output(self, domains):
		data = {'SOME':[], 'HIGH':[]}
		for d,v in domains.items():
			d_cats = [c for c in self.cat_dict[d] if len(c)>0 and len(c.split(' '))<3]
			overlap = float(len(v))/self.max_queries
			if 0.4 < overlap < 0.6:
				data['SOME'].append(d)
			elif overlap >= 0.6:
				data['HIGH'].append(d)
		data['href'] = self.urls
		json_data = json.dumps(data)
		print json_data
		sys.stdout.flush()
		

def main():
	text = sys.argv[1]
	try:
		language = sys.argv[2]
	except IndexError:
		language = 'english'
	sc = FoF(text, language)
	queries = sc.get_queries()
	domains = sc.get_urls(queries)
	sc.load_domains()
	sc.render_output(domains)

if __name__ == "__main__":
    main()
