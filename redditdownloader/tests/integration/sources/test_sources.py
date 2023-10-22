import os
from tests.mock import EnvironmentTest
import static.settings as settings
import sources


class SourceTest(EnvironmentTest):
	env = 'all_sources'

	def setUp(self):
		settings.load(self.settings_file)
		dfs = sources.DirectFileSource(file=os.path.join(self.dir, 'export.csv'), slow_fallback=True)
		settings.add_source(dfs, prevent_duplicate=True, save_after=False)

	def test_unique_types(self):
		""" Source types should be unqiue """
		types = []
		for s in sources.load_sources(None):
			self.assertTrue(s.type, f"Source is missing a type! {s.__class__.__name__}")
			self.assertNotIn(
				s.type,
				types,
				msg=f"Source type {s.type} is not unique! ({s.__class__.__name__})",
			)
			types.append(s.type)

	def test_unique_description(self):
		""" Source descriptions should be unique """
		types = []
		for s in sources.load_sources(None):
			self.assertTrue(
				s.description, f"Source is missing a description! {s.__class__.__name__}"
			)
			self.assertNotIn(
				s.description,
				types,
				msg=f"Source desc {s.description} is not unique! ({s.__class__.__name__})",
			)
			types.append(s.description)

	def test_settings_sources(self):
		""" Should properly load Sources from settings  """
		self.assertGreater(len(sources.all_sources()), 0, "Failed to load any Sources from settings file!")

	def test_config_summaries(self):
		""" All config summaries should work once loaded """
		for s in settings.get_sources():
			print(s.get_alias())
			self.assertTrue(
				s.get_config_summary(), f'Source {s.type} is missing a config summary!'
			)

	def test_load_elements(self):
		""" Loading elements should work for all Sources """
		for s in settings.get_sources():
			print(s)
			eles = list(s.get_elements())
			self.assertGreater(
				len(eles),
				0,
				f"Failed to load any elements from test Source: {s.get_alias()}",
			)
			self.assertTrue(all(eles), f"Loaded invalid RedditElements: {eles}")

	def test_to_obj(self):
		""" All sources should convert to objects """
		for s in settings.get_sources():
			self.assertTrue(s.to_obj(), f"Failed to decode Source: {s.type}")
			self.assertTrue(
				s.to_obj(for_webui=True), f"Failed to decode webui-Source for: {s.type}"
			)
