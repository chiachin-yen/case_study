"""Web enhanced case study."""

from argparse import ArgumentParser
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import errno
import json
import logging
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request

import image_utilities

__author__ = "Chia Chin Yen"
__version__ = "0.1.0"


# Beta parameters
user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) '
              'Gecko/20100101 Firefox/42.0')

# Logging
if not os.path.exists('log'):
    os.mkdir('log')
log_filename = os.path.join('log', datetime.now().strftime("%Y-%m-%d.log"))
logging.basicConfig(
    level=logging.DEBUG,
    format=u'%(asctime)s|%(name)-8s|%(levelname)-8s|%(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.FileHandler(log_filename, 'w', 'utf-8')])

# Define handler to output sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt=u'%(asctime)s,%(name)-8s,%(levelname)-8s,%(message)s',
    datefmt='%H:%M:%S')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Create arguments parser
arg_parser = ArgumentParser()
arg_parser.add_argument('url',
                        nargs='?',
                        help='url to fetch')
arg_parser.add_argument('-AD_id',
                        dest='ArchDaily_page_ID',
                        help='ArchDaily page ID')
arg_parser.add_argument('-AD_ca',
                        dest='ArchDaily_category',
                        help='ArchDaily project category')
arg_parser.add_argument('-AD_re',
                        dest='ArchDaily_re',
                        help='ArchDaily re-download images.')

class CaseStudy(object):
    """Basic tools."""

    def __init__(self):
        """Initialize class."""
        self.user_agent = ('Mozilla/5.0 '
                           '(Macintosh; Intel Mac OS X x.y; rv:42.0) '
                           'Gecko/20100101 Firefox/42.0')

    def get_html(self, url):
        """Return html content from thr given url."""
        request = urllib.request.Request(
            url, None, {'User-Agent': self.user_agent})

        try:
            response = urllib.request.urlopen(request)
            return response
        except urllib.error.HTTPError as e:
            logging.error(e)
            return False
        except urllib.error.URLError as e:
            logging.error('URLError')
            return False


class CaseCollector(object):
    """A tool for intense case study."""

    def __init__(self):
        """Initialize a collector."""
        self.Get_ArchDaily_article = True
        self.Get_ArchDaily_chart = True
        self.Get_ArchDaily_gallery = False
        self.ArchDaily_root = 'ArchDaily'

    def json_writer(self, path, meta=None):
        """Write json data."""
        try:
            with open(path, 'w', encoding='utf-8') as json_file:
                json.dump(meta, json_file, ensure_ascii=False)
            return True
        except Exception:
            return False

    def format_filename(self, input_str=None, space=True):
        """Format a string into a valid path name."""
        invalid_chars = '\\/<>:?*|\a\b\f\n\r\t\v'

        filename = input_str.replace('\"', '\'')
        for chrs in invalid_chars:
            filename = filename.replace(chrs, ' ')
        filename = filename.rstrip().lstrip()
        if not space:
            filename = filename.replace(' ', '_')

        return filename

    def url_fetcher(self, url=None):
        """WIP Fetcher."""
        logging.info('Scrapper Version : ' + __version__)
        logging.info('Input URL : ' + url)
        logging.info('Start Fetching at {}'.format(datetime.now()))

        # detect the website
        url_parser = urllib.parse.urlparse(url.lstrip())

        if url_parser.netloc == 'www.archdaily.com':
            logging.info('Detected website : ArchDaily')
            self.ArchDaily_Operation(url)
        else:
            logging.info('currently unknown website')

    def write_TXT(self, file=None, lines=None):
        """Write lines to the text file."""
        if file is not None:
            with open(file, 'w', encoding='utf-8') as TXT_file:
                if isinstance(lines, (tuple, list)):
                    for line in lines:
                        TXT_file.write(str(line) + '\n')
                else:
                    TXT_file.write(str(lines))

    def write_CSV(self, file=None, lines=None):
        """Write lines to the CSV file."""
        if file is not None:
            with open(file, 'a', encoding='utf-8', newline='') as CSV_file:
                csv_writer = csv.writer(CSV_file)
                csv_writer.writerows(lines)

    def log_TXT(self, file=None, lines=None):
        """Write a new line to the text file."""
        if file is not None:
            with open(file, 'a', encoding='utf-8') as TXT_file:
                TXT_file.write(str(lines) + '\n')

    def ArchDaily_Operation(
        self,
        url,
        get_article=True,
        get_gallery=True,
        get_data=True,
        summary=True
    ):
        """Fetch ArchDaily pages."""
        logging.info('Fetching mode : ArchDaily')

        # Parse the url
        ArchDaily_url = urllib.parse.urlparse(url.lstrip())

        # Get page ID
        page_id = str(ArchDaily_url.path.split('/')[1])
        logging.info('Page ID : ' + page_id)

        # Trim the query string in the url
        query = urllib.parse.parse_qs(ArchDaily_url.query)
        query.pop('q2', None)
        ArchDaily_url = ArchDaily_url._replace(query='')
        ArchDaily_url = urllib.parse.urlunparse(ArchDaily_url)
        logging.info("Trimmed url: "+ArchDaily_url)

        # Check the fetching summary
        summary_path = os.path.join(self.ArchDaily_root, 'AD_summary.csv')
        headers = ['ID', 'type', 'article', 'gallery', 'data',
                   'fetcher_ver', 'time', 'path', 'url']

        # Create a dictionary to record fetching status
        fetch_result = dict.fromkeys(headers, False)

        # Read the fetching history
        id_found = -1
        if summary:
            if os.path.exists(summary_path):
                with open(summary_path, 'r',
                          encoding='utf-8', newline='') as summary_file:
                    summary_reader = csv.DictReader(summary_file)
                    logging.debug('summary path exist')
                    for i, row in enumerate(summary_reader, 1):
                        if page_id == row['ID']:
                            id_found = i
                            logging.info('ID founded at line '+str(id_found))
                            # Check previous fetching status
                            if row['fetcher_ver'] != __version__:
                                logging.critical('different fetcher version, '
                                                 'recommanding manual check.')
                                return False

                            else:
                                if row['article'] == 'True':
                                    fetch_result['article'] = True
                                    get_article = False
                                if row['gallery'] == 'True':
                                    fetch_result['gallery'] = True
                                    get_gallery = False
                                if row['data'] == 'True':
                                    fetch_result['data'] = True
                                    get_data = False
                            break

            # Create a summary file if there is none
            else:
                if not os.path.exists(self.ArchDaily_root):
                    os.makedirs(self.ArchDaily_root)
                with open(summary_path, 'w',
                          encoding='utf-8', newline='') as summary_file:
                    summary_writer = csv.DictWriter(
                        summary_file, fieldnames=headers)
                    summary_writer.writeheader()

        # New ID detected
        if id_found < 0:
            logging.info('New ID detected.')
        else:
            if all(v is False for v in [get_article, get_data, get_gallery]):
                logging.warning('Nothing new to fetch.')
                return False

        # fetch html and parse it for category info
        try:
            logging.info('Fetching : '+ArchDaily_url)
            html_response = self.get_html(url=ArchDaily_url).read()
        except Exception:
            logging.warning('download html failed')
            return False

        # Create BeautifulSoup parser once for all
        bs_parser = BeautifulSoup(html_response, 'html.parser')

        # Get ArchDaily category data
        category_data = self.ArchDaily_get_category(bs_parser)

        # Add more information in data
        category_data['page_id'] = page_id
        if ('Text description '
                'provided by the architects.') in bs_parser.article.text:
            category_data['text_provided_by_architects'] = True
        else:
            category_data['text_provided_by_architects'] = False
        category_data['article_date'] = self.Archdaily_time_string(bs_parser)

        # make path
        if category_data['AD_article_type'] == 'Projects':
            save_path = os.path.join(
                self.ArchDaily_root,
                category_data['AD_article_type'],
                category_data['categories'],
                self.ArchDaily_naming(category_data['project_name'])
            )
        elif category_data['AD_article_type'] == 'News':
            save_path = os.path.join(
                self.ArchDaily_root,
                category_data['AD_article_type'],
                self.ArchDaily_naming(category_data['project_name'])
            )
        elif category_data['AD_article_type'] == 'Articles':
            save_path = os.path.join(
                self.ArchDaily_root,
                category_data['AD_article_type'],
                self.ArchDaily_naming(category_data['project_name'])
            )

        else:
            logging.warning('Currently unsupported AD page types')
            return False

        # make directory
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        # Update fetching result with known parameters
        fetch_result['path'] = save_path
        fetch_result['ID'] = page_id
        fetch_result['url'] = ArchDaily_url
        fetch_result['type'] = category_data['AD_article_type']
        fetch_result['fetcher_ver'] = __version__
        fetch_result['time'] = datetime.now()

        # save html file
        with open(os.path.join(save_path, page_id+'-page.html'),
                  'wb') as html_file:
            html_file.write(html_response)

        if get_data:
            if self.json_writer(
                    os.path.join(save_path, page_id + '-data.json'),
                    category_data):
                fetch_result['data'] = True
            else:
                logging.warning('Failed to fetch data')

        if get_gallery:
            # Fetch gallery
            if self.ArchDaily_gallery(save_path, page_id, bs_parser):
                fetch_result['gallery'] = True
            else:
                logging.warning('Failed to fetch gallery')
        else:
            # save links for future fetching
            self.ArchDaily_gallery(
                save_path, page_id, bs_parser, link_only=True)

        if get_article:
            # Including chart file
            self.ArchDaily_chart(os.path.join(
                save_path, '{}-chart.json'.format(page_id)), bs_parser)

            # Fetch article last, its function will somehow broke parser
            if self.ArchDaily_article(os.path.join(
                    save_path, '{}-article.txt'.format(page_id)), bs_parser):
                fetch_result['article'] = True

        # Save url file
        self.save_url(
            os.path.join(save_path, page_id + '-link.html'),
            ArchDaily_url)

        # Write the result to the summary
        if summary:
            if int(id_found) >= 0:
                # Delete previous record then add new one
                inline = None
                with open(summary_path, 'r', encoding='utf-8') as prev_summary:
                    inline = prev_summary.readlines()
                with open(summary_path, 'w', encoding='utf-8') as outfile:
                    line_num = int(id_found)
                    for index, line in enumerate(inline):
                        if index != line_num:
                            outfile.write(line)
                        else:
                            logging.debug('deleting line ' + str(index))

            with open(summary_path, 'a',
                      encoding='utf-8', newline='') as summary_file:
                summary_writer = csv.DictWriter(
                    summary_file, fieldnames=headers)
                summary_writer.writerow(fetch_result)
                logging.critical('Fetching Success')

        return True

    def ArchDaily_chart(self, path, bs_parser):
        """Find the chart item in ArchDaily."""
        chart = {}
        for AD_char_item in bs_parser.find_all('h3', class_='afd-char-title'):
            chart[AD_char_item.text.strip()] = (
                AD_char_item.find_next().text.strip())

        if chart is not None:
            self.json_writer(path, chart)
            return chart
        else:
            logging.warning('Find no chart')
            return False

    def ArchDaily_naming(self, title_str):
        """Rename the title from ArchDaily."""
        str_by = 'by'
        str_on = 'on'
        new_title = str_by.join(title_str.rsplit('/', 1))
        new_title = str_on.join(new_title.rsplit('|', 1))
        new_title = self.format_filename(new_title)
        return new_title

    def ArchDaily_article(self, path, bs_parser):
        """Find the article in ArchDaily."""
        # Test if article is content_legacy
        article = bs_parser.find('div', id='content_legacy')
        if article is None:
            article = bs_parser.find('article')

        # remove tags except tags in white list
        all_tags = [tag.name for tag in article.find_all()]
        tag_list = list(set(all_tags))
        white_list = ['p', 'a', 'b']
        for tag in white_list:
            if tag in tag_list:
                tag_list.remove(tag)
        for no_tag in tag_list:
            for soup in article(no_tag):
                soup.extract()

        # combine text in paragraph
        text = article.text.strip()

        if len(text) > 0:
            self.write_TXT(path, text)
            return True
        else:
            logging.warning('Get empty article')
            return False

    def ArchDaily_gallery(self, path, page_id, bs_parser, link_only=False):
        """Fetch ArchDaily Gallery images."""
        all_link = []
        for i, gallery_item in enumerate(
                bs_parser.find_all('a', class_='gallery-thumbs-link'), 1):
            for item in gallery_item.find_all('img'):
                if 'alt' in item.attrs:
                    img_desc = self.format_filename(item['alt'])
                    # Truncate name if it exceed maxium char num of 72
                    if len(img_desc) > 72:
                        img_desc = (img_desc[:69] + '(S)')

                    image_name = '{}-image{}-{}.jpg'.format(
                        page_id, i, self.format_filename(img_desc)
                    )
                else:
                    image_name = '{}-image{}.jpg'.format(page_id, i)

                image_url = str(
                    item['data-src']).replace('thumb_jpg', 'large_jpg')

                # Trim the query string in the url
                image_url = urllib.parse.urlparse(image_url.lstrip())
                image_url = image_url._replace(query='')
                image_url = urllib.parse.urlunparse(image_url)

                image_filename = os.path.join(path, image_name)

                if not link_only:
                    if not os.path.isfile(image_filename):
                        try:
                            req = urllib.request.Request(
                                image_url, headers={'User-Agent': user_agent})
                            temp_img = urllib.request.urlopen(req)
                            with open(image_filename, 'wb') as img_file:
                                img_file.write(temp_img.read())
                            logging.info(image_name + ' Downloaded')
                        except Exception as e:
                            logging.error('Failed to download ' + image_url)
                            logging.error('error msg: ' + str(e))
                            return False
                        time.sleep(abs(random.normalvariate(3, 1)))
                else:
                    all_link.append(image_url+'\t'+image_name)

        if link_only:
            self.write_TXT(
                os.path.join(path, page_id + '-image_url.txt'),
                all_link)

        return True

    def ArchDaily_re_gallery(self, dir_path):
        """Download all image in an previously fetched AD pages
        with version before 0.1.0.
        """
        for (dirpath, dirnames, filenames) in os.walk(dir_path):
            for filename in filenames:
                if "-page.html" in filename:
                    finish = os.path.join(dirpath, 'finished.txt')
                    if not os.path.isfile(finish):
                        page_id = filename.split('-')[0]
                        fp = os.path.join(dirpath, filename)
                        with open(fp, 'r', encoding='utf-8') as f:
                            image_parser = BeautifulSoup(
                                f.read(),
                                'html.parser')
                            if self.ArchDaily_gallery(
                                path=dirpath,
                                page_id=page_id,
                                bs_parser=image_parser,
                                link_only=False
                            ):
                                with open(finish, 'w') as f:
                                    pass

    def Archdaily_time_string(self, bs_parser):
        """Fetch the date string in AD article."""
        time_string = bs_parser.find('li', class_='theDate')
        if time_string is None:
            return False
        else:
            return time_string.text

    def ArchDaily_get_category(self, bs_parser=None):
        """Fetch Archdaily Category items."""
        if bs_parser is not None:
            category = {}
            for a in bs_parser.find_all('li', class_="afd-breadcrumbs__item"):
                item = a.find('a')
                href_string = item['href']
                if href_string == '':
                    category['project_name'] = item.text.strip()
                elif href_string == '/news':
                    category['AD_article_type'] = item.text.strip()
                elif href_string == '/articles':
                    category['AD_article_type'] = 'Articles'
                else:
                    item_type = href_string.split('/')[-2]
                    if item_type == '':
                        category['media'] = item.text.strip()
                    elif item_type == 'search':
                        category['AD_article_type'] = item.text.strip()
                    elif item_type == 'categories':
                        category['categories'] = item.text.strip()
                    elif item_type == 'country':
                        category['country'] = item.text.strip()
                    elif item_type == 'offices':
                        category['offices'] = item.text.strip()
                    elif item_type == 'year':
                        category['year'] = item.text.strip()

            # Fill blank fields
            if 'categories' not in category:
                category['categories'] = 'unknown category'
            if 'country' not in category:
                category['country'] = 'unknown country'
            if 'offices' not in category:
                category['offices'] = 'unknown office'
            if 'year' not in category:
                category['year'] = 'unknown year'

            for key, value in category.items():
                logging.info(
                    u'category result of {}: {}'.format(key, value))
            return category
        else:
            return False

    def Archdaily_ID_to_url(self, page_id):
        """Append id to ArchDaily url."""
        return("https://www.archdaily.com/"+str(page_id))

    def save_url(self, path, url=''):
        """Save a html with original link."""
        with open(path, 'w', encoding='utf-8') as link_file:
            link_file.write(
                '<!DOCTYPE html><html><head>'
                '<meta http-equiv=\"refresh\" content=\"0; url={!s}\">'
                '</head><body></body></html>'.format(url))

    def get_html(self, url):
        """Return a downloaded html object."""
        # initiate fetching
        logging.info('Downloading html')
        request = urllib.request.Request(url, None, {'User-Agent': user_agent})

        try:
            response = urllib.request.urlopen(request)
            return response
        except urllib.error.HTTPError as e:
            logging.error(e)
            return False
        except urllib.error.URLError as e:
            logging.error('URLError')
            return False
        '''
        except httplib.HTTPException, e:
            checksLogger.error('HTTPException')
        except Exception:
            import traceback
            checksLogger.error('generic exception: ' + traceback.format_exc())
        '''


class AD_page_getter(object):
    """Extract links from ArchDaily."""

    def __init__(self, interval=2):
        """Initialize class instance."""
        self.interval = interval

    def AD_project_by_category(self, category, start=1, pages=-1,
                               rand_interval=True):
        """Harvest all project by category."""
        url = ('https://www.archdaily.com/search/projects/'
               'categories/{}?page=').format(category)

        i = start
        while i < start+pages or pages < 0:
            logging.info('Fetching search result page ' + str(i))
            search_links = self.AD_link_from_page(url + str(i))
            if search_links == []:
                break
            else:
                for result in search_links:
                    yield 'https://www.archdaily.com'+result['href']

            if rand_interval:
                time.sleep(abs(random.normalvariate(5, 2)))
            else:
                time.sleep(self.interval)

            i += 1

        logging.critical('searching ends at page ' + str(i - 1))

        return True

    def AD_link_from_page(self, url):
        """Extract links from page."""
        logging.info('Downloading html')
        request = urllib.request.Request(url, None, {'User-Agent': user_agent})

        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            logging.error(e)
            return False
        except urllib.error.URLError as e:
            logging.error('URLError')
            return False

        bs_parser = BeautifulSoup(response.read(), 'html.parser')
        search_links = bs_parser.find_all('a', class_='afd-search-list__link')
        return search_links


if __name__ == '__main__':
    getter = AD_page_getter(interval=0)
    fetcher = CaseCollector()
    args = arg_parser.parse_args()
    if args.ArchDaily_page_ID is not None:
        fetcher.ArchDaily_Operation(
            fetcher.Archdaily_ID_to_url(args.ArchDaily_page_ID),
            summary=False)

    elif args.ArchDaily_category is not None:
        for page_url in getter.AD_project_by_category(
                category=args.ArchDaily_category):
            time.sleep(abs(random.normalvariate(5, 2)))
            fetcher.ArchDaily_Operation(page_url, summary=True)

    elif args.ArchDaily_page_ID is None:
        while True:
            input_ID = input('ArchDaily Page ID: ')
            get_image = input('Download image? (y/n): ')
            if input_ID != '':
                if get_image == 'n':
                    fetcher.ArchDaily_Operation(
                        fetcher.Archdaily_ID_to_url(input_ID),
                        get_gallery=False,
                        summary=False)
                else:
                    fetcher.ArchDaily_Operation(
                        fetcher.Archdaily_ID_to_url(input_ID),
                        summary=False)

            else:
                break

    else:
        fetcher.ArchDaily_Operation(args.url, summary=False)
