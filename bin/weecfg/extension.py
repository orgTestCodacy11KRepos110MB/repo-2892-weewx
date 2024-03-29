#
#    Copyright (c) 2009-2023 Tom Keffer <tkeffer@gmail.com> and Matthew Wall
#
#    See the file LICENSE.txt for your full rights.
#
"""Utilities for installing and removing extensions"""

import glob
import os
import shutil
import sys
import tempfile

import configobj

import weecfg
import weeutil.config
import weeutil.weeutil
from weecfg import Logger
from weewx import all_service_groups

# Very old extensions did:
#   from setup import ExtensionInstaller
# Redirect references to 'setup' to me instead.
sys.modules['setup'] = sys.modules[__name__]


class InstallError(Exception):
    """Exception raised when installing an extension."""


class ExtensionInstaller(dict):
    """Base class for extension installers."""

    def configure(self, engine):
        """Can be overridden by installers. It should return True if the installer modifies
        the configuration dictionary."""
        return False


class ExtensionEngine(object):
    """Engine that manages extensions."""
    # Extension components can be installed to these locations
    target_dirs = {
        'bin': 'BIN_DIR',
        'skins': 'SKIN_DIR'}

    def __init__(self, config_path, config_dict, dry_run=False, logger=None):
        """
        Initializer for ExtensionEngine.

        Args:
        
            config_path (str): Path to the configuration file.  For example, something
                         like /home/weewx/weewx.conf)

            config_dict (str): The configuration dictionary, i.e., the contents of the
                         file at config_path.

            dry_run (bool): If Truthy, all the steps will be printed out, but nothing will
                     actually be done.

            logger (weecfg.Logger): An instance of weecfg.Logger. This will be used to print
                    things to the console.
        """
        self.config_path = config_path
        self.config_dict = config_dict
        self.logger = logger or Logger()
        self.dry_run = dry_run

        self.root_dict = weecfg.extract_roots(self.config_dict)
        self.logger.log("root dictionary: %s" % self.root_dict, 4)

    def enumerate_extensions(self):
        """Print info about all installed extensions to the logger."""
        ext_dir = self.root_dict['EXT_DIR']
        try:
            exts = os.listdir(ext_dir)
            if exts:
                self.logger.log("%-18s%-10s%s" % ("Extension Name", "Version", "Description"),
                                level=0)
                for f in exts:
                    info = self.get_extension_info(f)
                    msg = "%(name)-18s%(version)-10s%(description)s" % info
                    self.logger.log(msg, level=0)
            else:
                self.logger.log("Extension cache is '%s'" % ext_dir, level=2)
                self.logger.log("No extensions installed", level=0)
        except OSError:
            self.logger.log("No extension cache '%s'" % ext_dir, level=2)
            self.logger.log("No extensions installed", level=0)

    def get_extension_info(self, ext_name):
        ext_cache_dir = os.path.join(self.root_dict['EXT_DIR'], ext_name)
        _, installer = weecfg.get_extension_installer(ext_cache_dir)
        return installer

    def install_extension(self, extension_path):
        """Install an extension.

        Args:
            extension_path(str): Either a file path, a directory path, or an URL.
        """
        self.logger.log("Request to install '%s'" % extension_path)
        if self.dry_run:
            self.logger.log("This is a dry run. Nothing will actually be done.")

        # Figure out what extension_path is
        if extension_path.startswith('http'):
            # It's an URL. Download, then install
            import urllib.request
            import tempfile
            # Download the file into a temporary file
            with tempfile.NamedTemporaryFile() as test_fd:
                filename, info = urllib.request.urlretrieve(extension_path, test_fd.name)
                # Now install the temporary file. The file type will be given up the download
                # header's "subtype". This will be something like "zip".
                extension_name = self._install_from_file(test_fd.name, info.get_content_subtype())
        elif os.path.isfile(extension_path):
            # It's a file. Figure out what kind, then install. If it's not a zipfile, assume
            # it's a tarfile.
            if extension_path[-4:] == '.zip':
                filetype = 'zip'
            else:
                filetype = 'tar'
            extension_name = self._install_from_file(extension_path, filetype)
        elif os.path.isdir(extension_path):
            # It's a directory. Install directly.
            extension_name = self.install_from_dir(extension_path)
        else:
            raise InstallError(f"Unrecognized type for {extension_path}")

        self.logger.log(f"Finished installing extension {extension_name} from {extension_path}")
        if self.dry_run:
            self.logger.log("This was a dry run. Nothing was actually done.")

    def _install_from_file(self, filepath, filetype):
        """Install the extension at path filepath."""
        # Make a temporary directory into which to extract the file.
        with tempfile.TemporaryDirectory() as dir_name:
            if filetype == 'zip':
                member_names = weecfg.extract_zip(filepath, dir_name, self.logger)
            else:
                # Assume it's a tarfile
                member_names = weecfg.extract_tar(filepath, dir_name, self.logger)
            extension_reldir = os.path.commonprefix(member_names)
            if not extension_reldir:
                raise InstallError(f"Unable to install from {filepath}: no common path "
                                   "(the extension archive contains more than a "
                                   "single root directory)")
            extension_dir = os.path.join(dir_name, extension_reldir)
            extension_name = self.install_from_dir(extension_dir)

        return extension_name

    def install_from_dir(self, extension_dir):
        """Install the extension whose components are in extension_dir"""
        self.logger.log("Request to install extension found in directory %s" %
                        extension_dir, level=2)

        # The "installer" is actually a dictionary containing what is to be installed and where.
        # The "installer_path" is the path to the file containing that dictionary.
        installer_path, installer = weecfg.get_extension_installer(extension_dir)
        extension_name = installer.get('name', 'Unknown')
        self.logger.log("Found extension with name '%s'" % extension_name,
                        level=2)

        # Go through all the files used by the extension. A "source tuple" is something like
        # (bin, [user/myext.py, user/otherext.py]). The first element is the directory the files go
        # in, the second element is a list of files to be put in that directory
        self.logger.log("Copying new files", level=2)
        N = 0
        for source_tuple in installer['files']:
            # For each set of sources, see if it's a type we know about
            for directory in ExtensionEngine.target_dirs:
                # This will be something like 'bin', or 'skins':
                source_type = os.path.commonprefix((source_tuple[0], directory))
                # If there is a match, source_type will be something other than an empty string:
                if source_type:
                    # This will be something like 'BIN_DIr' or 'SKIN_DIR':
                    root_type = ExtensionEngine.target_dirs[source_type]
                    # Now go through all the files of the source tuple
                    for install_file in source_tuple[1]:
                        source_path = os.path.join(extension_dir, install_file)
                        dst_file = ExtensionEngine._strip_leading_dir(install_file)
                        destination_path = os.path.abspath(os.path.join(self.root_dict[root_type],
                                                                        dst_file))
                        self.logger.log("Copying from '%s' to '%s'"
                                        % (source_path, destination_path),
                                        level=3)
                        if not self.dry_run:
                            try:
                                os.makedirs(os.path.dirname(destination_path))
                            except OSError:
                                pass
                            shutil.copy(source_path, destination_path)
                            N += 1
                    # We've completed at least one destination directory that we recognized.
                    break
            else:
                # No 'break' occurred, meaning that we didn't recognize any target directories.
                sys.exit("Unknown destination directory %s. Skipped file(s) %s"
                         % (source_tuple[0], source_tuple[1]))
        self.logger.log("Copied %d files" % N, level=2)

        save_config = False

        # Go through all the possible service groups and see if the extension
        # includes any services that belong in any of them.
        self.logger.log("Adding services to service lists", level=2)
        for service_group in all_service_groups:
            if service_group in installer:
                extension_svcs = weeutil.weeutil.option_as_list(installer[service_group])
                # Be sure that the leaf node is actually a list
                svc_list = weeutil.weeutil.option_as_list(
                    self.config_dict['Engine']['Services'][service_group])
                for svc in extension_svcs:
                    # See if this service is already in the service group
                    if svc not in svc_list:
                        if not self.dry_run:
                            # Add the new service into the appropriate service group
                            svc_list.append(svc)
                            self.config_dict['Engine']['Services'][service_group] = svc_list
                            save_config = True
                        self.logger.log("Added new service %s to %s"
                                        % (svc, service_group), level=3)

        # Give the installer a chance to do any customized configuration
        save_config |= installer.configure(self)

        # Look for options that have to be injected into the configuration file
        if 'config' in installer:
            save_config |= self._inject_config(installer['config'], extension_name)

        # Save the extension's install.py file in the extension's installer
        # directory for later use enumerating and uninstalling
        extension_installer_dir = os.path.join(self.root_dict['EXT_DIR'], extension_name)
        self.logger.log("Saving installer file to %s" % extension_installer_dir)
        if not self.dry_run:
            try:
                os.makedirs(os.path.join(extension_installer_dir))
            except OSError:
                pass
            shutil.copy2(installer_path, extension_installer_dir)

        if save_config:
            backup_path = weecfg.save_with_backup(self.config_dict, self.config_path)
            self.logger.log("Saved configuration dictionary. Backup copy at %s" % backup_path)

        return extension_name

    def get_lang_code(self, skin, default_code):
        """Convenience function for picking a language code"""
        skin_path = os.path.join(self.root_dict['SKIN_DIR'], skin)
        languages = weecfg.get_languages(skin_path)
        code = weecfg.pick_language(languages, default_code)
        return code

    def _inject_config(self, extension_config, extension_name):
        """Injects any additions to the configuration file that the extension might have.
        
        Returns True if it modified the config file, False otherwise.
        """
        self.logger.log("Adding sections to configuration file", level=2)
        # Make a copy so we can modify the sections to fit the existing configuration
        if isinstance(extension_config, configobj.Section):
            cfg = weeutil.config.deep_copy(extension_config)
        else:
            cfg = dict(extension_config)

        save_config = False

        # Extensions can specify where their HTML output goes relative to HTML_ROOT. So, we must
        # prepend the installation's HTML_ROOT to get a final location that the reporting engine
        # can use. For example, if an extension specifies "HTML_ROOT=forecast", the final location
        # might be public_html/forecast, or /var/www/html/forecast, depending on the installation
        # method.
        ExtensionEngine.prepend_path(cfg, 'HTML_ROOT', self.config_dict['StdReport']['HTML_ROOT'])

        # If the extension uses a database, massage it so it's compatible with the new V3.2 way of
        # specifying database options
        if 'Databases' in cfg:
            for db in cfg['Databases']:
                db_dict = cfg['Databases'][db]
                # Does this extension use the V3.2+ 'database_type' option?
                if 'database_type' not in db_dict:
                    # There is no database type specified. In this case, the driver type better
                    # appear. Fail hard, with a KeyError, if it does not. Also, if the driver is
                    # not for sqlite or MySQL, then we don't know anything about it. Assume the
                    # extension author knows what s/he is doing, and leave it be.
                    if db_dict['driver'] == 'weedb.sqlite':
                        db_dict['database_type'] = 'SQLite'
                        db_dict.pop('driver')
                    elif db_dict['driver'] == 'weedb.mysql':
                        db_dict['database_type'] = 'MySQL'
                        db_dict.pop('driver')

        if not self.dry_run:
            # Inject any new config data into the configuration file
            weeutil.config.conditional_merge(self.config_dict, cfg)

            self._reorder(cfg)
            save_config = True

        self.logger.log("Merged extension settings into configuration file", level=3)
        return save_config

    def _reorder(self, cfg):
        """Reorder the resultant config_dict"""
        # Patch up the location of any reports so they appear before FTP/RSYNC

        # First, find the FTP or RSYNC reports. This has to be done on the basis of the skin type,
        # rather than the report name, in case there are multiple FTP or RSYNC reports to be run.
        try:
            for report in self.config_dict['StdReport'].sections:
                if self.config_dict['StdReport'][report]['skin'] in ['Ftp', 'Rsync']:
                    target_name = report
                    break
            else:
                # No FTP or RSYNC. Nothing to do.
                return
        except KeyError:
            return

        # Now shuffle things so any reports that appear in the extension appear just before FTP (or
        # RSYNC) and in the same order they appear in the extension manifest.
        try:
            for report in cfg['StdReport']:
                weecfg.reorder_sections(self.config_dict['StdReport'], report, target_name)
        except KeyError:
            pass

    def uninstall_extension(self, extension_name):
        """Uninstall the extension with name extension_name"""

        self.logger.log("Request to remove extension '%s'" % extension_name)
        if self.dry_run:
            self.logger.log("This is a dry run. Nothing will actually be done.")

        # Find the subdirectory containing this extension's installer
        extension_installer_dir = os.path.join(self.root_dict['EXT_DIR'], extension_name)
        try:
            # Retrieve it
            _, installer = weecfg.get_extension_installer(extension_installer_dir)
        except weecfg.ExtensionError:
            sys.exit("Unable to find extension %s" % extension_name)

        # Remove any files that were added:
        self.uninstall_files(installer)

        save_config = False

        # Remove any services we added
        for service_group in all_service_groups:
            if service_group in installer:
                new_list = [x for x in self.config_dict['Engine']['Services'][service_group] \
                            if x not in installer[service_group]]
                if not self.dry_run:
                    self.config_dict['Engine']['Services'][service_group] = new_list
                    save_config = True

        # Remove any sections we added
        if 'config' in installer and not self.dry_run:
            weecfg.remove_and_prune(self.config_dict, installer['config'])
            save_config = True

        if not self.dry_run:
            # Finally, remove the extension's installer subdirectory:
            shutil.rmtree(extension_installer_dir)

        if save_config:
            weecfg.save_with_backup(self.config_dict, self.config_path)

        self.logger.log("Finished removing extension '%s'" % extension_name)

    def uninstall_files(self, installer):
        """Delete files that were installed for this extension"""

        directory_list = []

        self.logger.log("Removing files.", level=2)
        N = 0
        for source_tuple in installer['files']:
            # For each set of sources, see if it's a type we know about
            for directory in ExtensionEngine.target_dirs:
                # This will be something like 'bin', or 'skins':
                source_type = os.path.commonprefix((source_tuple[0], directory))
                # If there is a match, source_type will be something other than an empty string:
                if source_type:
                    # This will be something like 'BIN_DIR' or 'SKIN_DIR':
                    root_type = ExtensionEngine.target_dirs[source_type]
                    # Now go through all the files of the source tuple
                    for install_file in source_tuple[1]:
                        dst_file = ExtensionEngine._strip_leading_dir(install_file)
                        destination_path = os.path.abspath(os.path.join(self.root_dict[root_type],
                                                                        dst_file))
                        file_name = os.path.basename(destination_path)
                        # There may be a versioned skin.conf. Delete it by adding a wild card.
                        # Similarly, be sure to delete Python files with .pyc or .pyo extensions.
                        if file_name == 'skin.conf' or file_name.endswith('py'):
                            destination_path += "*"
                        N += self.delete_file(destination_path)
                    # Accumulate all directories under 'skins'
                    if root_type == 'SKIN_DIR':
                        dst_dir = ExtensionEngine._strip_leading_dir(source_tuple[0])
                        directory = os.path.abspath(os.path.join(self.root_dict[root_type],
                                                                 dst_dir))
                        directory_list.append(directory)
                    break
            else:
                sys.exit("Skipped file %s: Unknown destination directory %s"
                         % (source_tuple[1], source_tuple[0]))
        self.logger.log("Removed %d files" % N, level=2)

        # Now delete all the empty skin directories. Start by finding the directory closest to root
        most_root = os.path.commonprefix(directory_list)
        # Now delete the directories under it, from the bottom up.
        for dirpath, _, _ in os.walk(most_root, topdown=False):
            if dirpath in directory_list:
                self.delete_directory(dirpath)

    def delete_file(self, filename, report_errors=True):
        """
        Delete files from the file system.

        Args:
            filename (str): The path to the file(s) to be deleted. Can include wildcards.

            report_errors (bool): If truthy, report an error if the file is missing or cannot be
                deleted. Otherwise don't. In neither case will an exception be raised.
        Returns:
            int: The number of files deleted
        """
        n_deleted = 0
        for fn in glob.glob(filename):
            self.logger.log("Deleting file %s" % fn, level=2)
            if not self.dry_run:
                try:
                    os.remove(fn)
                    n_deleted += 1
                except OSError as e:
                    if report_errors:
                        self.logger.log("Delete failed: %s" % e, level=4)
        return n_deleted

    def delete_directory(self, directory, report_errors=True):
        """
        Delete the given directory from the file system.

        Args:

            directory (str): The path to the directory to be deleted. If the directory is not
                empty, nothing is done.

            report_errors (bool); If truthy, report an error. Otherwise don't. In neither case will
                an exception be raised. """
        try:
            if os.listdir(directory):
                self.logger.log("Directory '%s' not empty" % directory, level=2)
            else:
                self.logger.log("Deleting directory %s" % directory, level=2)
                if not self.dry_run:
                    shutil.rmtree(directory)
        except OSError as e:
            if report_errors:
                self.logger.log("Delete failed on directory '%s': %s"
                                % (directory, e), level=2)

    @staticmethod
    def _strip_leading_dir(path):
        idx = path.find('/')
        if idx >= 0:
            return path[idx + 1:]

    @staticmethod
    def prepend_path(a_dict: dict, label: str, value: str) -> None:
        """Prepend the value to every instance of the label in dict a_dict"""
        for k in a_dict:
            if isinstance(a_dict[k], dict):
                ExtensionEngine.prepend_path(a_dict[k], label, value)
            elif k == label:
                a_dict[k] = os.path.join(value, a_dict[k])

    # def transfer(self, root_src_dir):
    #     """For transfering contents of an old 'user' directory into the new one."""
    #     if not os.path.isdir(root_src_dir):
    #         sys.exit(f"{root_src_dir} is not a directory")
    #     root_dst_dir = self.root_dict['USER_DIR']
    #     self.logger.log(f"Transferring contents of {root_src_dir} to {root_dst_dir}", 1)
    #     if self.dry_run:
    #         self.logger.log(f"This is a {bcolors.BOLD}dry run{bcolors.ENDC}. "
    #                         f"Nothing will actually be done.")
    #
    #     for dirpath, dirnames, filenames in os.walk(root_src_dir):
    #         if os.path.basename(dirpath) in {'__pycache__', '.init'}:
    #             self.logger.log(f"Skipping {dirpath}.", 3)
    #             continue
    #         dst_dir = dirpath.replace(root_src_dir, root_dst_dir, 1)
    #         self.logger.log(f"Making directory {dst_dir}", 3)
    #         if not self.dry_run:
    #             os.makedirs(dst_dir, exist_ok=True)
    #         for f in filenames:
    #             if ".pyc" in f:
    #                 self.logger.log(f"Skipping {f}", 3)
    #                 continue
    #             dst_file = os.path.join(dst_dir, f)
    #             if os.path.exists(dst_file):
    #                 self.logger.log(f"File {dst_file} already exists. Not replacing.", 2)
    #             else:
    #                 src_file = os.path.join(dirpath, f)
    #                 self.logger.log(f"Copying file {src_file} to {dst_dir}", 3)
    #                 if not self.dry_run:
    #                     shutil.copy(src_file, dst_dir)
    #     if self.dry_run:
    #         self.logger.log("This was a dry run. Nothing was actually done")
