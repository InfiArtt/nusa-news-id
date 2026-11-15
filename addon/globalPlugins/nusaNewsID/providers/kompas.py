# kompas.py
#
# Kompas (kompas.com). It has no working feed, so every category reads a page.
# Each section is a subdomain, which keeps the categories apart.

from .baseProvider import BaseProvider, CategorySource

# Domestic news comes from many subdomains (nasional, regional, megapolitan, city sites),
# so "Nasional" takes every subdomain except those of other categories and non-news sections.
_DOMESTIC = (
	r"//(?!(?:entertainment|money|tekno|bola|otomotif|lifestyle|health|travel|edukasi|internasional"
	r"|properti|lestari|video|jeo|tren|sains|food|parapuan|kolom|go|pemilu|interaktif)\.)[a-z]+\.kompas\.com/"
)


class KompasProvider(BaseProvider):
	source_name = "Kompas"
	base_url = "https://www.kompas.com"
	# Example: https://nasional.kompas.com/read/2026/11/15/07000081/dalang-di-balik-penyadapan
	article_pattern = r"kompas\.com/read/\d{4}/\d{2}/\d{2}/\d+"
	# The path holds the date, and the first six digits of the number the time: 07000081 is 07:00:00.
	url_date_pattern = r"kompas\.com/read/(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})(\d{2})"
	categories = {
		"Nasional": CategorySource(html="https://news.kompas.com", sections=_DOMESTIC),
		"Internasional": CategorySource(
			html="https://internasional.kompas.com", sections=r"//internasional\.kompas\.com/"
		),
		"Teknologi": CategorySource(html="https://tekno.kompas.com", sections=r"//tekno\.kompas\.com/"),
		"Politik": CategorySource(html="https://nasional.kompas.com", sections=r"//nasional\.kompas\.com/"),
		"Ekonomi": CategorySource(html="https://money.kompas.com", sections=r"//money\.kompas\.com/"),
		"Olahraga": CategorySource(html="https://bola.kompas.com", sections=r"//bola\.kompas\.com/"),
		"Entertainment": CategorySource(
			html="https://entertainment.kompas.com", sections=r"//entertainment\.kompas\.com/"
		),
		"Disabilitas": CategorySource(html="https://www.kompas.com/tag/disabilitas"),
	}
