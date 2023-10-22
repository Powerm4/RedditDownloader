import re
import csv
from psaw import PushshiftAPI
from sources.source import Source
from processing.wrappers.redditelement import RedditElement
from static.praw_wrapper import get_info


class DirectFileSource(Source):
	def __init__(self, file=None, slow_fallback=False):
		super().__init__(source_type='direct-csv-source', description="Process a CSV file.")
		self.data['file'] = file
		self.data['slow_fallback'] = slow_fallback
		self._ps = None

	def get_elements(self):
		self._ps = PushshiftAPI()
		with open(self.data['file'], newline='', encoding='utf-8') as csvfile:
			reader = csv.reader(csvfile)
			header = next(reader)
			rows = enumerate(reader)
			while True:
				subs = []
				comments = []
				for idx, row in rows:
					if not (idx + 1) % 101:
						break
					row = dict(zip(header, row))
					if row['direction'] == 'up':
						isPost = not re.search(r'/comments/.+?/.+?/([a-zA-Z0-9]+)/?', row['permalink'])
						if isPost:
							subs.append(row['id'])
						else:
							comments.append(row['id'])
				if len(comments):
					yield from self.get_comments(comments)
				if len(subs):
					yield from self.get_subs(subs)
				if not len(comments) and not len(subs):
					break

	def get_comments(self, comments):
		found = list(self._ps.search_comments(ids=comments, limit=len(comments)))
		subs = list(self._ps.search_submissions(limit=len(found), ids=[c.link_id.replace('t3_', '', 1) for c in found]))
		for s in subs:
			search = list(filter(lambda c: c.link_id.replace('t3_', '', 1) == s.id, found))
			if not search:
				print('Failed to locate comment using parent ID!', s.id)
				continue
			com = search[0]
			found.remove(com)
			comments = list(filter(lambda c: c.replace('t1_', '', 1) != com.id.replace('t1_', '', 1), comments))
			yield RedditElement(com, ext_submission_obj=s)
		if self.data['slow_fallback'] and len(comments):
			for comm in get_info([f't1_{c}' for c in comments]):
				yield RedditElement(comm)

	def get_subs(self, subs):
		for post in self._ps.search_submissions(ids=subs, limit=len(subs)):
			subs = list(filter(lambda s: s != post.id.replace('t3_', '', 1), subs))
			p = RedditElement(post)
			if self.check_filters(p):
				yield p
		if self.data['slow_fallback'] and len(subs):
			for comm in get_info([f't3_{c}' for c in subs]):
				yield RedditElement(comm)

	def get_config_summary(self):
		return f"""Reading from CSV "{self.data['file']}". Using slow direct backup: {self.data['slow_fallback']}"""
