import re
import html
from collections import OrderedDict
from lxml import html as lxhtml, etree
from processing.handlers import HandlerResponse
from processing.wrappers import http_downloader


tag = 'tumblr'
order = 2
regex = r"(?:https?)?(?::\/\/)?(?:www.)?(.+?)\.tumblr\.com\/post\/(\d+)"


def _iprop(ele, ele_tag, default=99999):
	return int(ele.get(ele_tag)) if ele.get(ele_tag) else default


def get_media_urls(base, post_id):
	url = f'https://{base}.tumblr.com/api/read?id={post_id}'
	data = http_downloader.open_request(url, stream=False)
	if not data or data.status_code != 200:
		return []
	# noinspection PyUnresolvedReferences
	tree = etree.fromstring(data.content)
	post = tree.find('posts').find('post')
	found = []
	for vid in post.findall('video-player'):
		ht = html.unescape(vid.text)
		ve = lxhtml.fromstring(ht)
		if vid.get('max-width') and found:
			continue  # Skip videos with this dimension if we've already found the base link.
		if ve.get('src'):
			found.append(ve.get('src').strip())
		found.extend(src.get('src').strip() for src in ve.findall('source'))
	photo_eles = []
	if post.find('.//photoset') is None:
		photo_eles.append(post)
	else:
		photo_eles.extend(post.findall('.//photo'))
	for img in photo_eles:
		srcs = sorted(img.findall('photo-url'), key=lambda x: _iprop(x, 'max-width'), reverse=True)
		if len(srcs):
			found.append(srcs[0].text.strip())
	# Some people embed additional media in the description, so check for that:
	captions = filter(lambda x: x is not None, [post.find(s) for s in ['.//video-caption', './/photo-caption']])
	for c in captions:
		capt = lxhtml.fromstring(html.unescape(c.text))
		found.extend(
			img.get('src') for img in capt.findall('.//img') if img.get('src')
		)
	return list(OrderedDict.fromkeys(found).keys())


def handle(task, progress):
	m = re.match(regex, task.url)
	if m is None or '.media.tumblr' in task.url:
		return False
	gr = m.groups()
	progress.set_status("Parsing Tumblr page...")
	# noinspection PyBroadException
	try:
		if urls := get_media_urls(gr[0], gr[1]):
			return (
				HandlerResponse(success=True, handler=tag, album_urls=urls)
				if len(urls) > 1
				else http_downloader.download_binary(urls[0], task.file, progress, tag)
			)
		else:
			return None
	except Exception as ex:
		# print('Tumblr: ERROR:', ex, task.url, file=sys.stderr, flush=True)
		return False


