import os
import glob
from gnr.core.gnrbag import Bag
from gnr.core.gnrsys import expandpath
from gnr.core.gnrlang import uniquify, GnrException
from collections import defaultdict
from gnr.app.gnrconfig import MenuStruct
from gnr.app.gnrconfig import getGnrConfig, setEnvironment


    
class EntityNotFoundException(GnrException):
    pass
    

    
class UnknownEntityTypeException(GnrException):
    pass
    

class PathResolver(object):
    """TODO"""
    entities = dict(
            instance='instances',
            site='sites',
            resource='resources',
            package='packages',
            project='projects')
            
    def __init__(self, gnr_config=None):
        self.gnr_config = gnr_config or getGnrConfig()
        setEnvironment(self.gnr_config)
        
        
                
    def js_path(self, lib_type='gnr', version='11'):
        """TODO Return the configuration static js path, with *lib_type* and *version* specified
        
        :param lib_type: Genro Javascript library == gnr
        :param version: the Genro Javascript library version related to the Dojo one. The number of Dojo
                        version is written without any dot. E.g: '11' is in place of '1.1'"""
        path = self.gnr_config['gnr.environment_xml.static.js.%s_%s?path' % (lib_type, version)]
        if path:
            path = os.path.join(expandpath(path), 'js')
        return path
        
    def entity_name_to_path(self, entity_name, entity_type, look_in_projects=True):
        """TODO
        
        :param entity_name: TODO
        :param entity_type: TODO
        :param look_in_projects: TODO"""
        entity = self.entities.get(entity_type)
        if not entity:
            raise UnknownEntityTypeException('Error: entity type %s not known' % entity_type)
        if entity in self.gnr_config['gnr.environment_xml']:
            for path in [expandpath(path) for path in
                         self.gnr_config['gnr.environment_xml'].digest('%s:#a.path' % entity) if
                         os.path.isdir(expandpath(path))]:
                entity_path = os.path.join(path, entity_name)
                if os.path.isdir(entity_path):
                    return expandpath(entity_path)
        if look_in_projects and 'projects' in self.gnr_config['gnr.environment_xml']:
            projects = [expandpath(path) for path in self.gnr_config['gnr.environment_xml'].digest('projects:#a.path')
                        if os.path.isdir(expandpath(path))]
            for project_path in projects:
                for path in glob.glob(os.path.join(project_path, '*/%s' % entity)):
                    entity_path = os.path.join(path, entity_name)
                    if os.path.isdir(entity_path):
                        return expandpath(entity_path)
        raise EntityNotFoundException('Error: %s %s not found' % (entity_type, entity_name))
        
    def site_name_to_path(self, site_name):
        """TODO
        
        :param site_name: TODO"""
        return self.entity_name_to_path(site_name, 'site')

    def get_siteconfig(self,site_name):
        return Bag(os.path.join(self.site_name_to_path(site_name),'siteconfig.xml'))
        
    def instance_name_to_path(self, instance_name):
        """TODO
        
        :param instance_name: TODO"""
        return self.entity_name_to_path(instance_name, 'instance')
        
    def package_name_to_path(self, package_name):
        """TODO
        
        :param package_name: TODO"""
        return self.entity_name_to_path(package_name, 'package')
        
    def resource_name_to_path(self, resource_name):
        """TODO
        
        :param resource_name: TODO"""
        return self.entity_name_to_path(resource_name, 'resource')
        
    def project_name_to_path(self, project_name):
        """TODO
        
        :param project_name: TODO"""
        return self.entity_name_to_path(project_name, 'project', look_in_projects=False)
        
    def project_repository_name_to_path(self, project_repository_name, strict=True):
        """TODO
        
        :param project_repository_name: TODO
        :param strict: TODO"""
        if not strict or 'gnr.environment_xml.projects.%s' % project_repository_name in self.gnr_config:
            path = self.gnr_config['gnr.environment_xml.projects.%s?path' % project_repository_name]
            if path:
                return expandpath(path)
        else:
            raise EntityNotFoundException('Error: Project Repository %s not found' % project_repository_name)
            
class ProjectMaker(object):
    """Handle the autocreation of a package.
    
    To autocreate a package, please type in your console::
        
        gnrmkpackage packagename
        
    where ``packagename`` is the name of your ``package`` folder."""
    def __init__(self, project_name, base_path=None):
        self.project_name = project_name
        self.base_path = base_path or '.'
        
    def do(self):
        """Create the project path with its subfolders paths: the path of the ``packages`` folder,
        the path of the ``sites`` folder, the path of the ``instances`` folder and the path of the
        ``resources`` folder."""
        self.project_path = os.path.join(self.base_path, self.project_name)
        self.packages_path = os.path.join(self.project_path, 'packages')
        self.sites_path = os.path.join(self.project_path, 'sites')
        self.instances_path = os.path.join(self.project_path, 'instances')
        self.resources_path = os.path.join(self.project_path, 'resources')
        for path in (self.project_path, self.packages_path, self.sites_path, self.instances_path, self.resources_path):
            if not os.path.isdir(path):
                os.mkdir(path)
                
class SiteMaker(object):
    """Handle the autocreation of the ``sites`` folder.
    
    To autocreate the ``sites`` folder, please type in your console::
        
        gnrmksite sitesname
        
    where 'sitesname' is the name of your ``sites`` folder.
    """
    def __init__(self, site_name, base_path=None, resources=None, instance=None, dojo_version='11',
                 wsgi_port=None, wsgi_reload=None, wsgi_mainpackage=None, wsgi_debug=None, config=None):
        self.site_name = site_name
        self.base_path = base_path or '.'
        self.resources = resources or []
        self.instance = instance
        self.wsgi_port = wsgi_port
        self.wsgi_reload = wsgi_reload
        self.wsgi_mainpackage = wsgi_mainpackage
        self.wsgi_debug = wsgi_debug
        self.dojo_version = dojo_version
        self.config = config
        
    def do(self):
        """TODO"""
        self.site_path = os.path.join(self.base_path, self.site_name)
        pages_path = os.path.join(self.site_path, 'pages')
        root_py_path = os.path.join(self.site_path, 'root.py')
        siteconfig_xml_path = os.path.join(self.site_path, 'siteconfig.xml')
        if not os.path.isdir(self.site_path):
            os.mkdir(self.site_path)
        if not os.path.isdir(pages_path):
            os.mkdir(pages_path)
        if not os.path.isfile(root_py_path):
            root_py = open(root_py_path, 'w')
            root_py.write("""#!/usr/bin/env python2.6
import sys
sys.stdout = sys.stderr
from gnr.web.gnrwsgisite import GnrWsgiSite
site = GnrWsgiSite(__file__)

def application(environ,start_response):
    return site(environ,start_response)

if __name__ == '__main__':
    from gnr.web.server import NewServer
    server=NewServer(__file__)
    server.run()""")
            root_py.close()
        if not os.path.isfile(siteconfig_xml_path):
            if not self.config:
                siteconfig = Bag()
                if self.instance:
                    siteconfig.setItem('instances.%s' % self.instance, None)
                for resource in self.resources:
                    if isinstance(resource, tuple) or isinstance(resource, list):
                        resource, resource_path = resource
                        siteconfig.setItem('resources.%s' % resource, None, path=resource_path)
                    else:
                        siteconfig.setItem('resources.%s' % resource, None)
                wsgi_options = dict()
                for option in ('reload', 'debug', 'port', 'mainpackage'):
                    value = getattr(self, 'wsgi_%s' % option, None)
                    if value:
                        wsgi_options[option] = value
                siteconfig.setItem('wsgi', None, **wsgi_options)
                siteconfig['connection_timeout'] = None
                siteconfig['connection_refresh'] = None
                siteconfig.setItem('dojo', None, version=self.dojo_version)
            else:
                siteconfig = self.config
            siteconfig.toXml(siteconfig_xml_path,typevalue=False,pretty=True)
            
class InstanceMaker(object):
    """Handle the autocreation of the ``instances`` folder.
    
    To autocreate the ``instances`` folder, please type in your console::
        
        gnrmkinstance instancesname
        
    where ``instancesname`` is the name of your ``instances`` folder.
    """
    def __init__(self, instance_name, base_path=None, packages=None, authentication=True, authentication_pkg=None,
                 db_dbname=None, db_implementation=None, db_host=None, db_port=None,
                 db_user=None, db_password=None, use_dbstores=False, config=None):
        self.instance_name = instance_name
        self.base_path = base_path or '.'
        self.packages = packages or []
        self.db_dbname = db_dbname or instance_name
        self.authentication = authentication
        if self.authentication:
            self.authentication_pkg = authentication_pkg
            if not self.authentication_pkg and self.packages:
                package = self.packages[0]
                if isinstance(package, tuple) or isinstance(package, list):
                    package = package[0]
                self.authentication_pkg = package
            if not self.authentication_pkg:
                self.authentication_pkg = 'adm'
        self.db_implementation = db_implementation
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.use_dbstores = use_dbstores
        self.config = config

    def do(self):
        """TODO"""
        self.instance_path = os.path.join(self.base_path, self.instance_name)
        custom_path = os.path.join(self.instance_path, 'custom')
        data_path = os.path.join(self.instance_path, 'data')
        instanceconfig_xml_path = os.path.join(self.instance_path, 'instanceconfig.xml')
        folders_to_make = [self.instance_path, custom_path, data_path]
        if self.use_dbstores:
            dbstores_path = os.path.join(self.instance_path, 'dbstores')
            folders_to_make.append(dbstores_path)
        for path in folders_to_make:
            if not os.path.isdir(path):
                os.mkdir(path)
        if not os.path.isfile(instanceconfig_xml_path):
            if not self.config:
                instanceconfig = Bag()
                db_options = dict()
                for option in ('dbname', 'implementation', 'host', 'port', 'username', 'password'):
                    value = getattr(self, 'db_%s' % option, None)
                    if value:
                        db_options[option] = value
                instanceconfig.setItem('db', None, **db_options)
                instanceconfig.setItem('packages', None)
                for package in self.packages:
                    if isinstance(package, tuple) or isinstance(package, list):
                        package, package_path = package
                        instanceconfig.setItem('packages.%s' % package.replace(':','_'), None, path=package_path,pkgcode=package)
                    else:
                        instanceconfig.setItem('packages.%s' % package.replace(':','_'), None,pkgcode=package)
                if self.authentication:
                    instanceconfig.setItem('authentication', None, pkg=self.authentication_pkg)
                    instanceconfig.setItem('authentication.py_auth', None, defaultTags="user", pkg="adm",
                                           method="authenticate")
            else:
                instanceconfig = self.config
            instanceconfig.toXml(instanceconfig_xml_path,typevalue=False,pretty=True)
            
class PackageMaker(object):
    """Handle the autocreation of the ``packages`` folder.
    
    To autocreate the ``packages`` folder, please type in your console::
        
        gnrmkpackage packagesname
        
    where ``packagesname`` is the name of your ``packages`` folder.
    """
    def __init__(self, package_name, base_path=None, sqlschema=None, sqlprefix=True,
                 name_short=None, name_long=None, name_full=None,
                 login_url=None, comment=None,helloworld=False):
        self.package_name = package_name
        self.base_path = base_path or '.'
        self.name_short = name_short or self.package_name.capitalize()
        self.name_full = name_full or self.package_name.capitalize()
        self.name_long = name_long or self.package_name.capitalize()
        self.sqlschema = sqlschema or self.package_name.lower()
        self.sqlprefix = sqlprefix
        self.comment = comment or '%s package' % self.package_name
        self.login_url = login_url or '%s/login' % self.package_name
        self.helloworld = helloworld
        self.package_path = os.path.join(self.base_path, self.package_name)
        self.model_path = os.path.join(self.package_path, 'model')
        self.lib_path = os.path.join(self.package_path, 'lib')
        self.webpages_path = os.path.join(self.package_path, 'webpages')
        self.resources_path = os.path.join(self.package_path, 'resources')
        self.framedindex_path = os.path.join(self.webpages_path,'index.py')
        self.main_py_path = os.path.join(self.package_path, 'main.py')
        
    def do(self):
        """Creates the files of the ``packages`` folder"""
        for path in (self.package_path, self.model_path, self.lib_path, self.webpages_path, self.resources_path):
            if not os.path.isdir(path):
                os.mkdir(path)
        sqlprefixstring = ''
        if not os.path.exists(self.main_py_path):
            if self.sqlprefix is not None:
                if self.sqlprefix not in (True, False):
                    self.sqlprefix = "'%s'" % self.sqlprefix
                sqlprefixstring = "sqlprefix=%s,"%(self.sqlprefix)
            main_py_options = dict(comment=self.comment, sqlschema=self.sqlschema, sqlprefixstring=sqlprefixstring, name_short=self.name_short,
                                   name_long=self.name_long, name_full=self.name_full, login_url=self.login_url)
            main_py = open(self.main_py_path, 'w')
            main_py.write("""#!/usr/bin/env python
# encoding: utf-8
from gnr.app.gnrdbo import GnrDboTable, GnrDboPackage

class Package(GnrDboPackage):
    def config_attributes(self):
        return dict(comment='%(comment)s',sqlschema='%(sqlschema)s',%(sqlprefixstring)s
                    name_short='%(name_short)s', name_long='%(name_long)s', name_full='%(name_full)s')
                    
    def config_db(self, pkg):
        pass
        
class Table(GnrDboTable):
    pass
""" % main_py_options)
            main_py.close()

        if not os.path.exists(self.framedindex_path):
            with open(self.framedindex_path, 'w') as indexpage:
                indexpage.write("""# -*- coding: UTF-8 -*-
            
class GnrCustomWebPage(object):
    py_requires = 'plainindex'
    """)
        if self.helloworld:
            with open(os.path.join(self.webpages_path,'hello_world.py'), 'w') as helloworld:
                helloworld.write("""# -*- coding: UTF-8 -*-
            
class GnrCustomWebPage(object):
    def main(self,root,**kwargs):
        root.h1('Hello world',text_align='center')
    """)
            
class ResourceMaker(object):
    """Handle the creation of the ``resources`` folder"""
    def __init__(self, resource_name, base_path=None):
        self.resource_name = resource_name
        self.base_path = base_path or '.'
        
    def do(self):
        """TODO"""
        self.resource_path = os.path.join(self.base_path, self.resource_name)
        for path in (self.resource_path, ):
            if not os.path.isdir(path):
                os.mkdir(path)
        
class ThPackageResourceMaker(object):
    def __init__(self,application,package=None,tables=None,force=False,menu=False,columns=2,guess_size=False,indent=4):
        self.option_force = force
        self.option_menu = menu
        self.option_columns = columns
        self.option_guess_size = guess_size
        self.option_indent = indent
        self.pkg_tables = defaultdict(list)
        self.app = application 
        self.package = package
        self.tables = tables if tables else self.app.db.packages[self.package].tables.keys() 
        self.packageFolder = self.app.packages(package).packageFolder

    
    def makeResources(self):
        for table in self.tables:
            self.createResourceFile(table)
        if self.option_menu:
            self.makeMenu()

    def makeMenu(self):
        with open(os.path.join(self.packageFolder,'menu.py'),'w') as out_file:
            self.out_file = out_file
            self.writeHeaders()
            self.write('def config(root,application=None):')
            pkgobj =  self.app.db.package(self.package)
            self.write("%s = root.branch('%s')"%(self.package,(pkgobj.name_long or self.package.capitalize())),indent=1) 
            hasLookups = False
            for t in self.tables:
                tblobj = self.app.db.table('%s.%s' %(self.package,t))
                if tblobj.attributes.get('lookup'):
                    hasLookups = True
                else:
                    self.write("%s.thpage('%s',table='%s')" %(self.package,(tblobj.name_plural or tblobj.name_long or tblobj.name.capitalize()),
                            tblobj.fullname),indent=1)
            if hasLookups:
                self.write("%s.lookups('Lookup tables',lookup_manager='%s')" %(self.package,self.package),indent=1)


    def write(self,line=None, indent=0):
        line = line or ''
        self.out_file.write('%s%s\n'%(self.option_indent*indent*' ',line))

    def writeHeaders(self):
        self.write('#!/usr/bin/python')
        self.write('# -*- coding: UTF-8 -*-')
        self.write()
    
    def writeImports(self):
        self.write("from gnr.web.gnrbaseclasses import BaseComponent")
        self.write("from gnr.core.gnrdecorator import public_method")
        self.write()
    
    def writeViewClass(self, tblobj, columns):
        self.write("class View(BaseComponent):")
        self.write()
        self.write("def th_struct(self,struct):", indent=1)
        self.write('r = struct.view().rows()', indent=2)
        for column, size in columns:
            if self.option_guess_size:
                self.write("r.fieldcell('%s', width='%iem')"%(column,size), indent=2)
            else:
                self.write("r.fieldcell('%s')"%column, indent=2)
        self.write()
        self.write("def th_order(self):", indent=1)
        self.write("return '%s'"%columns[0][0], indent=2)
        self.write()
        self.write("def th_query(self):", indent=1)
        searchcol = tblobj.attributes.get('caption_field') 
        
        if not searchcol:
            l = filter(lambda c: c.attributes.get('dtype') in ('A','T','C') and not c.attributes.get('_sysfield'),tblobj.columns.values())
            if l:
                searchcol = l[0].name
        self.write("return dict(column='%s', op='contains', val='')"%searchcol, indent=2)
        self.write()
        self.write()
        self.write()

    def writeFormClass(self, tblobj, columns):
        children = self.getChildrenRelations(tblobj)
        self.write("class Form(BaseComponent):")
        self.write()
        self.write("def th_form(self, form):", indent=1)
        if children:
            self.write("bc = form.center.borderContainer()", indent=2)
            self.write("top = bc.contentPane(region='top',datapath='.record')", indent=2)
            self.write("fb = top.formbuilder(cols=%i, border_spacing='4px')"%self.option_columns, indent=2)
            for column, size in columns:
                self.write("fb.field('%s')"%column, indent=2)
            if len(children)>1:
                self.write("tc = bc.tabContainer(region='center',margin='2px')", indent=2)
                for c in children:
                    self.write("tab_%s = tc.contentPane(title='%s')" %(c.replace('@',''),(tblobj.name_plural or tblobj.name_long)), indent=2)
                    self.write("tab_%s.dialogTableHandler(relation='%s')" %(c.replace('@',''),c), indent=2)
            else:
                self.write("center = bc.contentPane(region='center')", indent=2)
                self.write("center.plainTableHandler(relation='%s')" %children[0], indent=2)
        else:
            self.write("pane = form.record", indent=2)
            self.write("fb = pane.formbuilder(cols=%i, border_spacing='4px')"%self.option_columns, indent=2)
            for column, size in columns:
                self.write("fb.field('%s')"%column, indent=2)
        self.write()
        self.write()
        self.write("def th_options(self):", indent=1)
        self.write("return dict(dialog_height='400px', dialog_width='600px')", indent=2)


    def getChildrenRelations(self,tblobj):
        result = []
        for relation,j in tblobj.relations.digest('#k,#a.joiner'):
            if j and j['mode'] == 'M' and j.get('onDelete') == 'cascade':
                result.append(relation)
        return result

    def createResourceFile(self, table):
        resourceFolder = os.path.join(self.packageFolder,'resources', 'tables', table)
        if not os.path.exists(resourceFolder):
            os.makedirs(resourceFolder)
        name = 'th_%s.py'%table
        path = os.path.join(resourceFolder, name)
        if os.path.exists(path) and not self.option_force:
            print '%s exist: will be skipped, use -f/--force to force replace' % name
            return
        columns = []
        max_size = 35
        tbl_obj =  self.app.db.table('%s.%s'%(self.package,table))
        for col_name,column in tbl_obj.columns.items():
            if column.attributes.get('_sysfield') or column.dtype in ('X','O'): 
                continue
            if column.dtype=='A':
                size = column.attributes.get('size','')
                if size:
                    if ':' in size:
                        size =size.split(':')[1]
                else:
                    size=max_size
                size = max(int(size),max_size)
            else:
                size = 7
            columns.append((column.name,size))
        with open(path,'w') as out_file:
            self.out_file = out_file
            self.writeHeaders()
            self.writeImports()
            self.writeViewClass(tbl_obj, columns)
            self.writeFormClass(tbl_obj, columns)
            print '%s created' % name


class ModWsgiMaker(object):
    """TODO"""
    pass

if __name__ == '__main__':
    pather = PathResolver()
    print pather.package_name_to_path('edicon')
    print pather.project_name_to_path('trasporti')
    print pather.instance_name_to_path('satlow')
    print pather.site_name_to_path('moscati')