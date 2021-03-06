from __future__ import unicode_literals, print_function
import os
import codecs
import logging
from glob import glob
from bs4 import BeautifulSoup
from libraries.general_tools.file_utils import write_file
from libraries.resource_container.ResourceContainer import RC
from libraries.general_tools.file_utils import load_yaml_object
from libraries.resource_container.ResourceContainer import BIBLE_RESOURCE_TYPES


def do_template(resource_type, source_dir, output_dir, template_file):
    if resource_type in BIBLE_RESOURCE_TYPES:
        templater = BibleTemplater(resource_type, source_dir, output_dir, template_file)
    elif resource_type == 'obs':
        templater = ObsTemplater(resource_type, source_dir, output_dir, template_file)
    elif resource_type == 'ta':
        templater = TaTemplater(resource_type, source_dir, output_dir, template_file)
    else:
        templater = Templater(resource_type, source_dir, output_dir, template_file)
    return templater.run()


class Templater(object):
    def __init__(self, resource_type, source_dir, output_dir, template_file):
        self.resource_type = resource_type
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.template_file = template_file  # Local file of template

        self.files = sorted(glob(os.path.join(self.source_dir, '*.html')))
        self.rc = None
        self.template_html = ''
        self.logger = logging.getLogger()

    def run(self):
        # get the resource container
        self.rc = RC(self.source_dir)
        with open(self.template_file) as template_file:
            self.template_html = template_file.read()
            soup = BeautifulSoup(self.template_html, 'html.parser')
            soup.body['class'] = soup.body.get('class', []) + [self.resource_type]
            if self.resource_type in BIBLE_RESOURCE_TYPES and self.resource_type != 'bible':
                soup.body['class'] = soup.body.get('class', []) + ['bible']
            self.template_html = unicode(soup)
        self.apply_template()
        return True

    def build_left_sidebar(self, filename=None):
        html = """
            <nav class="affix-top hidden-print hidden-xs hidden-sm" id="left-sidebar-nav">
                <div class="nav nav-stacked" id="revisions-div">
                    <h1>Revisions</h1>
                    <table width="100%" id="revisions"></table>
                </div>
            </nav>
            """
        return html

    def build_right_sidebar(self, filename=None):
        html = self.build_page_nav(filename)
        return html

    def build_page_nav(self, filename=None):
        html = """
            <nav class="affix-top hidden-print hidden-xs hidden-sm" id="right-sidebar-nav">
              <ul id="sidebar-nav" class="nav nav-stacked">
                <li><h1>Navigation</h1></li>
            """
        for fname in self.files:
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f, 'html.parser')
            if soup.find('h1'):
                title = soup.h1.text
            else:
                title = os.path.splitext(os.path.basename(fname))[0].replace('_', ' ').capitalize()
            if title == "Conversion requested..." or title == "Conversion successful" or title == "Index":
                continue
            if filename != fname:
                html += '<li><a href="{0}">{1}</a></li>'.format(os.path.basename(fname), title)
            else:
                html += '<li>{0}</li>'.format(title)
        html += """
                </ul>
            </nav>
            """
        return html

    def apply_template(self):
        language_code = self.rc.resource.language.identifier
        language_name = self.rc.resource.language.title
        language_dir = self.rc.resource.language.direction
        resource_title = self.rc.resource.title

        heading = '{0}: {1}'.format(language_name, resource_title)
        title = ''
        canonical = ''

        # soup is the template that we will replace content of for every file
        soup = BeautifulSoup(self.template_html, 'html.parser')
        left_sidebar_div = soup.body.find('div', id='left-sidebar')
        outer_content_div = soup.body.find('div', id='outer-content')
        right_sidebar_div = soup.body.find('div', id='right-sidebar')

        # find the outer-content div in the template
        if not outer_content_div:
            raise Exception('No div tag with id "outer-content" was found in the template')

        # get the canonical UTL
        if not canonical:
            links = soup.head.find_all('link[rel="canonical"]')
            if len(links) == 1:
                canonical = links[0]['href']

        # loop through the html files
        for filename in self.files:
            self.logger.debug('Applying template to {0}.'.format(filename))

            # read the downloaded file into a dom abject
            with codecs.open(filename, 'r', 'utf-8-sig') as f:
                fileSoup = BeautifulSoup(f, 'html.parser')

            # get the title from the raw html file
            if not title and fileSoup.head and fileSoup.head.title:
                title = fileSoup.head.title.text
            else:
                title = os.path.basename(filename)

            # get the language code, if we haven't yet
            if not language_code:
                if 'lang' in fileSoup.html:
                    language_code = fileSoup.html['lang']
                else:
                    language_code = 'en'

            # get the body of the raw html file
            if not fileSoup.body:
                body = BeautifulSoup('<div>No content</div>', 'html.parser').find('div').extract()
            else:
                body = fileSoup.body.extract()

            # insert new HTML into the template
            outer_content_div.clear()
            outer_content_div.append(body)
            soup.html['lang'] = language_code
            soup.html['dir'] = language_dir

            soup.head.title.clear()
            soup.head.title.append(heading+' - '+title)

            for a_tag in soup.body.find_all('a[rel="dct:source"]'):
                a_tag.clear()
                a_tag.append(title)

            # set the page heading
            heading_span = soup.body.find('span', id='h1')
            heading_span.clear()
            heading_span.append(heading)

            if left_sidebar_div:
                left_sidebar_html = self.build_left_sidebar(filename)
                left_sidebar = BeautifulSoup(left_sidebar_html, 'html.parser').nav.extract()
                left_sidebar_div.clear()
                left_sidebar_div.append(left_sidebar)

            if right_sidebar_div:
                right_sidebar_html = self.build_right_sidebar(filename)
                right_sidebar = BeautifulSoup(right_sidebar_html, 'html.parser').nav.extract()
                right_sidebar_div.clear()
                right_sidebar_div.append(right_sidebar)

            # render the html as an unicode string
            html = unicode(soup)

            # fix the footer message, removing the title of this page in parentheses as it doesn't get filled
            html = html.replace(
                '("<a xmlns:dct="http://purl.org/dc/terms/" href="https://live.door43.org/templates/project-page.html" rel="dct:source">{{ HEADING }}</a>") ',
                '')
            # update the canonical URL - it is in several different locations
            html = html.replace(canonical, canonical.replace('/templates/', '/{0}/'.format(language_code)))
            # write to output directory
            out_file = os.path.join(self.output_dir, os.path.basename(filename))
            self.logger.debug('Writing {0}.'.format(out_file))
            write_file(out_file, html.encode('ascii', 'xmlcharrefreplace'))


class ObsTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(ObsTemplater, self).__init__(*args, **kwargs)


class BibleTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(BibleTemplater, self).__init__(*args, **kwargs)

    def build_page_nav(self, filename=None):
        html = """
        <nav class="affix-top hidden-print hidden-xs hidden-sm" id="right-sidebar-nav">
            <ul id="sidebar-nav" class="nav nav-stacked books panel-group">
            """
        for fname in self.files:
            filebase = os.path.splitext(os.path.basename(fname))[0]
            # Getting the book code for HTML tag references
            fileparts = filebase.split('-')
            if len(fileparts) == 2:
                # Assuming filename of ##-<name>.usfm, such as 01-GEN.usfm
                book_code = fileparts[1].lower()
            else:
                # Assuming filename of <name.usfm, such as GEN.usfm
                book_code = fileparts[0].lower()
            book_code.replace(' ', '-').replace('.', '-')  # replacing spaces and periods since used as tag class
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.find('h1'):
                title = soup.find('h1').text
            else:
                title = '{0}.'.format(book_code)
            if title == "Conversion requested..." or title == "Conversion successful" or title == "Index":
                continue
            html += """
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a class="accordion-toggle" data-toggle="collapse" data-parent="#sidebar-nav" href="#collapse{0}">{1}</a>
                        </h4>
                    </div>
                    <div id="collapse{0}" class="panel-collapse collapse{2}">
                        <ul class="panel-body chapters">
                    """.format(book_code, title, ' in' if fname == filename else '')
            for chapter in soup.find_all('h2', {'c-num'}):
                html += """
                       <li class="chapter"><a href="{0}#{1}">{2}</a></li>
                    """.format(os.path.basename(fname) if fname != filename else '', chapter['id'],
                               chapter['id'].split('-')[2].lstrip('0'))
            html += """
                        </ul>
                    </div>
                </div>
                    """
        html += """
            </ul>
        </nav>
            """
        return html


class TaTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(TaTemplater, self).__init__(*args, **kwargs)
        self.section_container_id = 1

    def build_section_toc(self, section):
        """
        Recursive section toc builder
        :param dict section: 
        :return: 
        """
        if 'link' in section:
            link = section['link']
        else:
            link = 'section-container-{0}'.format(self.section_container_id)
            self.section_container_id = self.section_container_id + 1
        html = """
            <li>
                <a href="#{0}">{1}</a>
            """.format(link, section['title'])
        if 'sections' in section:
            html += """
                <ul>
            """
            for subsection in section['sections']:
                html += self.build_section_toc(subsection)
            html += """
                </ul>
            """
        html += """
            </li>
        """
        return html

    def build_page_nav(self, filename=None):
        self.section_container_id = 1
        html = """
            <nav class="affix-top hidden-print hidden-xs hidden-sm" id="right-sidebar-nav">
                <ul id="sidebar-nav" class="nav nav-stacked">
        """
        for fname in self.files:
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.find('h1'):
                title = soup.find('h1').text
            else:
                title = os.path.splitext(os.path.basename(fname))[0].title()
            if title == "Conversion requested..." or title == "Conversion successful" or title == "Index":
                continue
            if fname != filename:
                html += """
                <h4><a href="{0}">{1}</a></h4>
                """.format(os.path.basename(fname), title)
            else:
                html += """
                <h4>{0}</h4>
                """.format(title)
                toc = load_yaml_object(os.path.join('{0}-toc.yaml'.format(os.path.splitext(fname)[0])))
                if toc:
                    for section in toc['sections']:
                        html += self.build_section_toc(section)
                html += """
                """
        html += """
                </ul>
            </nav>
        """
        return html
