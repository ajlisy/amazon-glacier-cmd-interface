#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. module:: glacier.py
   :platform: Unix, Windows
   :synopsis: Command line interface for amazon glacier
"""

import sys
import os
##import select
import ConfigParser
import argparse
import re
##import json
##import logging
##import datetime
##import dateutil.parser
import locale
##import time
##import boto
##import glaciercorecalls
##import pytz

from prettytable import PrettyTable
from GlacierWrapper import GlacierWrapper
from functools import wraps

##MAX_VAULT_NAME_LENGTH = 255
##MAX_DESCRIPTION_LENGTH = 1024
##VAULT_NAME_ALLOWED_CHARACTERS = "[a-zA-Z\.\-\_0-9]+"
##DEFAULT_PART_SIZE = GlacierWrapper.DEFAULT_PART_SIZE

locale.setlocale(locale.LC_ALL, '') # Empty string = use default setting

##def progress(msg):
##    if sys.stdout.isatty():
##        print msg,
##        sys.stdout.flush()

##def check_vault_name(name):
##    m = re.match(VAULT_NAME_ALLOWED_CHARACTERS, name)
##    if len(name) > 255:
##        raise Exception(u"Vault name can be at most 255 characters long.")
##    if len(name) == 0:
##        raise Exception(u"Vault name has to be at least 1 character long.")
##    if m.end() != len(name):
##        raise Exception(u"Allowed characters are a–z, A–Z, 0–9, '_' (underscore), \
##'-' (hyphen), and '.' (period)")
##    return True



##
##def is_power_of_2(v):
##    return (v & (v - 1)) == 0
##
##def next_power_of_2(v):
##    """
##    Returns the next power of 2, or the argument if it's already a power of 2.
##    """
##    v -= 1
##    v |= v >> 1
##    v |= v >> 2
##    v |= v >> 4
##    v |= v >> 8
##    v |= v >> 16
##    return v + 1

def print_headers(headers):
    table = PrettyTable(["Header", "Value"])
    for header in headers:
        if len(str(header[1])) < 100:
            table.add_row(header)

    print table

##def parse_response(response):
##    if response.status == 403:
##        print "403 Forbidden."
##        print "\n"
##        print "Reason:"
##        print response.read()
##        print response.msg
##
##    print response.status, response.reason
##    if response.status == 204:
##        print_headers(response)

def default_glacier_wrapper(args):
    return GlacierWrapper(args.aws_access_key,
                          args.aws_secret_key,
                          args.region,
                          bookkeeping=args.bookkeeping,
                          bookkeeping_domain_name=args.bookkeeping_domain_name,
                          logfile=args.logfile,
                          loglevel=args.loglevel,
                          printtostdout=args.printtostdout)

def handle_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except GlacierWrapper.GlacierWrapperException as e:

            # We are only interested in the error message as it is a
            # self-caused exception.
            e.write(indentation='||  ', stack=False, message=True)
            sys.exit(1)

    return wrapper

@handle_errors
def lsvault(args):
    glacier = default_glacier_wrapper(args)
    vault_list = glacier.lsvault()
    table = PrettyTable(["Vault name", "ARN", "Created", "Size"])
    for vault in vault_list:
        table.add_row([vault['VaultName'],
                       vault['VaultARN'],
                       vault['CreationDate'],
                       locale.format('%d', vault['SizeInBytes'], grouping=True) ])
    table.sortby = "Vault name"
    print table

@handle_errors
def mkvault(args):
    glacier = default_glacier_wrapper(args)

    response = glacier.mkvault(args.vault)
    print dict(response)["location"]
    print print_headers(response)

@handle_errors
def rmvault(args):
    glacier = default_glacier_wrapper(args)

    response = glacier.rmvault(args.vault)
    print print_headers(response)

@handle_errors
def describevault(args):
    glacier = default_glacier_wrapper(args)

    response = glacier.describevault(args.vault)

    table = PrettyTable(["LastInventory", "Archives", "Size", "ARN", "Created"])
    table.add_row([response['LastInventoryDate'], response['NumberOfArchives'],
                   locale.format('%d', response['SizeInBytes'], grouping=True),
                   response['VaultARN'], response['CreationDate']])
    print table

@handle_errors
def listmultiparts(args):
    glacier = default_glacier_wrapper(args)

    response = glacier.listmultiparts(args.vault)
    if not response:
        print 'No active multipart uploads.'

    else:
        headers = sorted(response[0].keys())
        table = PrettyTable(headers)
        for entry in response:
            table.add_row([locale.format('%d', entry[k], grouping=True) if k == 'PartSizeInBytes'
                           else entry[k] for k in headers ])
        print table


##    print "Marker: ", response['Marker']
##    if len(response['UploadsList']) > 0:
##        headers = sorted(response['UploadsList'][0].keys())
##        table = PrettyTable(headers)
##        for entry in response['UploadsList']:
##            table.add_row([locale.format('%d', entry[k], grouping=True) if k == 'PartSizeInBytes'
##                           else entry[k] for k in headers ])
##        print table

@handle_errors
def abortmultipart(args):
    glacier = default_glacier_wrapper(args)
    
    response = glacier.abortmultipart(args.vault, args.uploadId)
    print_headers(response)

@handle_errors
def listjobs(args):
    glacier = default_glacier_wrapper(args)

    job_list = glacier.listjobs(args.vault)

    if job_list == []:
        print 'No jobs.'
    
    table = PrettyTable(["Action", "Archive ID", "Status", "Initiated",
                         "VaultARN", "Job ID"])
    for job in job_list:
        table.add_row([job['Action'],
                       job['ArchiveId'],
                       job['StatusCode'],
                       job['CreationDate'],
                       job['VaultARN'],
                       job['JobId']])
    print table

@handle_errors
def describejob(args):
    glacier = default_glacier_wrapper(args)
    gj = glacier.describejob(args.vault, args.jobid)

    print "Archive ID: %s\nJob ID: %s\nCreated: %s\nStatus: %s\n" % (gj['ArchiveId'],
                                                                     args.jobid, gj['CreationDate'],
                                                                     gj['StatusCode'])

### Formats file sizes in human readable format. Anything bigger than TB
### is returned is TB. Number of decimals is optional, defaults to 1.
##def size_fmt(num, decimals = 1):
##    fmt = "%%3.%sf %%s"% decimals
##    for x in ['bytes','KB','MB','GB']:
##        if num < 1024.0:
##            return fmt % (num, x)
##        
##        num /= 1024.0
##        
##    return fmt % (num, 'TB')

@handle_errors
def upload(args):
    glacier = default_glacier_wrapper(args)
    response = glacier.upload(args.vault, args.filename, args.description, args.region, args.stdin,
                              args.partsize)
    
##    glacierconn = glaciercorecalls.GlacierConnection(args.aws_access_key, args.aws_secret_key, region=region)
##
##    if BOOKKEEPING:
##        sdb_conn = boto.connect_sdb(aws_access_key_id=args.aws_access_key,
##                                    aws_secret_access_key=args.aws_secret_key)
##        domain_name = BOOKKEEPING_DOMAIN_NAME
##        try:
##            domain = sdb_conn.get_domain(domain_name, validate=True)
##        except boto.exception.SDBResponseError:
##            domain = sdb_conn.create_domain(domain_name)
##
##    if description:
##        description = " ".join(description)
##    else:
##        description = filename
##
##    if check_description(description):
##        reader = None
##
##        # If filename is given, try to use this file.
##        # Otherwise try to read data from stdin.
##        total_size = 0
##        if not stdin:
##            try:
##                reader = open(filename, 'rb')
##                total_size = os.path.getsize(filename)
##            except IOError:
##                print "Couldn't access the file given."
##                return False
##            
##        elif select.select([sys.stdin,],[],[],0.0)[0]:
##            reader = sys.stdin
##            total_size = 0
##        else:
##            print "Nothing to upload."
##            return False
##
##        if args.partsize < 0:
##            
##            # User did not specify part_size. Compute the optimal value.
##            if total_size > 0:
##                part_size = next_power_of_2(total_size / (1024*1024*10000))
##            else:
##                part_size = glaciercorecalls.GlacierWriter.DEFAULT_PART_SIZE / 1024 / 1024
##                
##        else:
##            part_size = next_power_of_2(args.partsize)
##
##        if total_size > part_size * 1024 * 1024 * 10000:
##            
##            # User specified a value that is too small. Adjust.
##            part_size = next_power_of_2(total_size / (1024*1024*10000))
##            print "WARNING: Part size given is too small; using %s MB parts to upload."% part_size
##
##        writer = glaciercorecalls.GlacierWriter(glacierconn, vault, description=description,
##                                                part_size=(part_size*1024*1024))
##
##        #Read file in chunks so we don't fill whole memory
##        start_time = current_time = previous_time = time.time()
##        for part in iter((lambda:reader.read(READ_PART_SIZE)), ''):
##
##            writer.write(part)
##            current_time = time.time()
##            overall_rate = int(writer.uploaded_size/(current_time - start_time))
##            if total_size > 0:
##                
##                # Calculate transfer rates in bytes per second.
##                current_rate = int(READ_PART_SIZE/(current_time - previous_time))
##
##                # Estimate finish time, based on overall transfer rate.
##                if overall_rate > 0:
##                    time_left = (total_size - writer.uploaded_size)/overall_rate
##                    eta = time.strftime("%H:%M:%S", time.localtime(current_time + time_left))
##                else:
##                    time_left = "Unknown"
##                    eta = "Unknown"
##                    
##                progress('\rWrote %s of %s (%s%%). Rate %s/s, average %s/s, eta %s.' %
##                         (size_fmt(writer.uploaded_size),
##                          size_fmt(total_size),
##                          int(100 * writer.uploaded_size/total_size),
##                          size_fmt(current_rate, 2),
##                          size_fmt(overall_rate, 2),
##                          eta))
##
##            else:
##                progress('\rWrote %s. Rate %s/s.' %
##                         (size_fmt(writer.uploaded_size),
##                          size_fmt(overall_rate, 2)))
##
##            previous_time = current_time
##
##        writer.close()
##        current_time = time.time()
##        overall_rate = int(writer.uploaded_size/(current_time - start_time))
##        progress('\rWrote %s. Rate %s/s.' %
##                 (size_fmt(writer.uploaded_size),
##                  size_fmt(overall_rate, 2)))
##
##        archive_id = writer.get_archive_id()
##        location = writer.get_location()
##        sha256hash = writer.get_hash()
##        if BOOKKEEPING:
##            file_attrs = {
##                'region':region,
##                'vault':vault,
##                'filename':filename,
##                'archive_id': archive_id,
##                'location':location,
##                'description':description,
##                'date':'%s' % datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
##                'hash':sha256hash
##            }
##
##            if args.name:
##                file_attrs['filename'] = args.name
##            elif stdin:
##                file_attrs['filename'] = description
##
##            domain.put_attributes(file_attrs['filename'], file_attrs)
##
##        print "Created archive with ID: ", archive_id
##        print "Archive SHA256 tree hash: ", sha256hash

@handle_errors
def getarchive(args):
    glacier = default_glacier_wrapper(args)
    response = glacier.getarchive(args.vault, args.archive)

    print response

    
##    region = args.region
##    vault = args.vault
##    archive = args.archive
##    filename = args.filename
##
##    glacierconn = glaciercorecalls.GlacierConnection(args.aws_access_key, args.aws_secret_key, region=region)
##    gv = glaciercorecalls.GlacierVault(glacierconn, vault)
##
##    jobs = gv.list_jobs()
##    found = False
##    for job in gv.job_list:
##        if job['ArchiveId'] == archive:
##            found = True
##            
##            # no need to start another archive retrieval
##            if filename or not job['Completed']:
##                print "ArchiveId: ", archive
##                
##            if job['Completed']:
##                job2 = glaciercorecalls.GlacierJob(gv, job_id=job['JobId'])
##                if filename:
##                    ffile = open(filename, "w")
##                    for part in iter((lambda:job2.get_output().read(READ_PART_SIZE)), ''):
##                        ffile.write(part)
##                    ffile.close()
##                else:
##                    print job2.get_output().read()
##                return
##            
##    if not found:
##        job = gv.retrieve_archive(archive)
##        print "Started"

@handle_errors
def download(args):
    glacier = default_glacier_wrapper(args)
    response = glacier.download(args.vault, args.archive, args.outfile, args.overwrite)
    if args.outfile:

        # Only print result when writing to file.
        print response

##    region = args.region
##    vault = args.vault
##    filename = args.filename
##    out_file = args.out_file
##
##    if not filename:
##        raise Exception(u"You must supply either a file name or a search\
##term to search the descriptions.")
##
##    args.search_term = filename
##    items = search(args, print_results=False)
##
##    n_items = 0
##    if not items:
##        print "No results."
##        return False
##
##    print "Region\tVault\tFilename\tArchive ID"
##    for item in items:
##        n_items += 1
##        archive = item['archive_id']
##        vault = item['vault']
##        print "%s\t%s\t%s\t%s" % (item['region'],
##                                  item['vault'],
##                                  item['filename'],
##                                  item['archive_id'])
##
##    if n_items > 1:
##        print "You need to uniquely identify file using region, vault and/or \
##the file name. Alternatively use getarchive <Archive ID> to retrieve \
##the archive."
##        return False
##
##    glacierconn = glaciercorecalls.GlacierConnection(args.aws_access_key, args.aws_secret_key, region=region)
##    gv = glaciercorecalls.GlacierVault(glacierconn, vault)
##
##    jobs = gv.list_jobs()
##    found = False
##    for job in gv.job_list:
##        if job['ArchiveId'] == archive:
##            found = True
##            
##            # no need to start another archive retrieval
##            if not job['Completed']:
##                print "Waiting for Amazon Glacier to retrieve the archive."
##                
##            if job['Completed']:
##                print "File is available, starting download now."
##                job2 = glaciercorecalls.GlacierJob(gv, job_id=job['JobId'])
##                if out_file:
##                    ffile = open(out_file, "w")
##                    ffile.write(job2.get_output().read())
##                    ffile.close()
##                else:
##                    print job2.get_output().read()
##
##            return True
##
##    if not found:
##        job = gv.retrieve_archive(archive)
##        print "Archive retrieve request sent to Amazon Glacier, your archive \
##be available for download in about four hours."

@handle_errors
def rmarchive(args):
    glacier = default_glacier_wrapper(args)
    glacier.rmarchive(args.vault, args.archive)
    print "archive removed."
    
##    region = args.region
##    vault = args.vault
##    archive = args.archive
##    BOOKKEEPING = args.bookkeeping
##    BOOKKEEPING_DOMAIN_NAME = args.bookkeeping_domain_name
##
##    if BOOKKEEPING:
##        sdb_conn = boto.connect_sdb(aws_access_key_id=args.aws_access_key,
##                                    aws_secret_access_key=args.aws_secret_key)
##        domain_name = BOOKKEEPING_DOMAIN_NAME
##        try:
##            domain = sdb_conn.get_domain(domain_name, validate=True)
##        except boto.exception.SDBResponseError:
##            domain = sdb_conn.create_domain(domain_name)
##
##    glacierconn = glaciercorecalls.GlacierConnection(args.aws_access_key, args.aws_secret_key, region=region)
##    gv = glaciercorecalls.GlacierVault(glacierconn, vault)
##
##    parse_response( gv.delete_archive(archive) )
##
##    # TODO: can't find a method for counting right now
##    query = 'select * from `%s` where archive_id="%s"' % (BOOKKEEPING_DOMAIN_NAME, archive)
##    items = domain.select(query)
##    for item in items:
##        domain.delete_item(item)

@handle_errors
def search(args, print_results=True):
    glacier = default_glacier_wrapper(args)
    response = glacier.search(vault=args.vault,
                              region=args.region,
                              search_term=args.search_term,
                              print_results=True)
    print response
    
##    region = args.region
##    vault = args.vault
##    search_term = args.search_term
##    BOOKKEEPING = args.bookkeeping
##    BOOKKEEPING_DOMAIN_NAME = args.bookkeeping_domain_name
##
##    if BOOKKEEPING:
##        sdb_conn = boto.connect_sdb(aws_access_key_id=args.aws_access_key,
##                                    aws_secret_access_key=args.aws_secret_key)
##        domain_name = BOOKKEEPING_DOMAIN_NAME
##        try:
##            domain = sdb_conn.get_domain(domain_name, validate=True)
##        except boto.exception.SDBResponseError:
##            domain = sdb_conn.create_domain(domain_name)
##            
##    else:
##        raise Exception(u"You must enable bookkeeping to be able to do searches.")
##
##    search_params = []
##    table_title = ""
##    if region:
##        search_params += ["region='%s'" % (region,)]
##    else:
##        table_title += "Region\t"
##
##    if vault:
##        search_params += ["vault='%s'" % (vault,)]
##    else:
##        table_title += "Vault\t"
##
##    table_title += "Filename\tArchive ID"
##
##    if search_term:
##        search_params += ["(filename like '"+ search_term+"%' or description like '"+search_term+"%')" ]
##
##    search_params = " and ".join(search_params)
##    query = 'select * from `%s` where %s' % (BOOKKEEPING_DOMAIN_NAME, search_params)
##    items = domain.select(query)
##
##    if print_results:
##        print table_title
##
##    for item in items:
##        
##        # print item, item.keys()
##        item_attrs = []
##        if not region:
##            item_attrs += [item[u'region']]
##            
##        if not vault:
##            item_attrs += [item[u'vault']]
##            
##        item_attrs += [item[u'filename']]
##        item_attrs += [item[u'archive_id']]
##        if print_results:
##            print "\t".join(item_attrs)
##
##    if not print_results:
##        return items

def render_inventory(inventory):
    print "Inventory of vault: %s" % (inventory["VaultARN"],)
    print "Inventory Date: %s\n" % (inventory['InventoryDate'],)
    print "Content:"
    table = PrettyTable(["Archive Description", "Uploaded", "Size", "Archive ID", "SHA256 hash"])
    for archive in inventory['ArchiveList']:
        table.add_row([archive['ArchiveDescription'],
                       archive['CreationDate'],
                       locale.format('%d', archive['Size'], grouping=True),
                       archive['ArchiveId'],
                       archive['SHA256TreeHash']])
    print table

def inventory(args):

    glacier = default_glacier_wrapper(args)
    response = glacier.inventory(args.vault, args.refresh)

    print response

##    
##    region = args.region
##    vault = args.vault
##    force = args.force
##    BOOKKEEPING = args.bookkeeping
##    BOOKKEEPING_DOMAIN_NAME = args.bookkeeping_domain_name
##
##    glacierconn = glaciercorecalls.GlacierConnection(args.aws_access_key, args.aws_secret_key, region=region)
##    gv = glaciercorecalls.GlacierVault(glacierconn, vault)
##    if force:
##        job = gv.retrieve_inventory(format="JSON")
##        print "Forced start of a new inventory retrieval job."
##        return True
##    
##    try:
##        gv.list_jobs()
##        inventory_retrievals_done = []
##        for job in gv.job_list:
##            if job['Action'] == "InventoryRetrieval" and job['StatusCode'] == "Succeeded":
##                d = dateutil.parser.parse(job['CompletionDate']).replace(tzinfo=pytz.utc)
##                job['inventory_date'] = d
##                inventory_retrievals_done += [job]
##
##        if len(inventory_retrievals_done):
##            list.sort(inventory_retrievals_done,
##                      key=lambda i: i['inventory_date'],
##                      reverse=True)
##            job = inventory_retrievals_done[0]
##            print "Inventory taken by JobId:", job['JobId']
##            job = glaciercorecalls.GlacierJob(gv, job_id=job['JobId'])
##            inventory = json.loads(job.get_output().read())
##
##            if BOOKKEEPING:
##                sdb_conn = boto.connect_sdb(aws_access_key_id=args.aws_access_key,
##                                            aws_secret_access_key=args.aws_secret_key)
##                domain_name = BOOKKEEPING_DOMAIN_NAME
##                try:
##                    domain = sdb_conn.get_domain(domain_name, validate=True)
##                except boto.exception.SDBResponseError:
##                    domain = sdb_conn.create_domain(domain_name)
##
##                d = dateutil.parser.parse(inventory['InventoryDate']).replace(tzinfo=pytz.utc)
##                item = domain.put_attributes("%s" % (d,), inventory)
##
##            if ((datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - d).days > 1):
##                gv.retrieve_inventory(format="JSON")
##                print "Started a new inventory retrieval job."
##        
##            render_inventory(inventory)
##        else:
##            job = gv.retrieve_inventory(format="JSON")
##            print "Started a new inventory retrieval job."
##            
##    except Exception, e:
##        print "exception: ", e
##        print json.loads(e[1])['message']

def setuplogging(args):
    printtostdout = args.printtostdout
    logfile = args.logfile
    loglevel = args.loglevel
    if not loglevel in ('3', 'CRITICAL', '2', 'ERROR',
                        '1', 'WARNING', '0', 'INFO',
                        '-1', 'DEBUG'):
        print 'Invalid loglevel; defaulting to level WARNING.'
        loglevel = 'WARNING'
    
##    printtostdout = args.printtostdout
##    logfile = args.logfile
##    loglevel = {'3': logging.CRITICAL,
##                'CRITICAL': logging.CRITICAL,
##                '2': logging.ERROR,
##                'ERROR': logging.ERROR,
##                '1': logging.WARNING,
##                'WARNING': logging.WARNING,
##                '0': logging.INFO,
##                'INFO': logging.INFO,
##                '-1': logging.DEBUG,
##                'DEBUG': logging.DEBUG
##                }[args.loglevel]
##
##    logging.basicConfig(level=loglevel,
##                        filename=logfile,
##                        format='%(levelname)-8s %(message)s')
##    
##    if printtostdout:
##        soh = logging.StreamHandler(sys.stderr)
##        soh.setLevel(loglevel)
##        logger = logging.getLogger()
##        logger.addHandler(soh)

def main():
    program_description = u"""
    Command line interface for Amazon Glacier
    """

    # Config parser
    conf_parser = argparse.ArgumentParser(
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                add_help=False)

    conf_parser.add_argument("-c", "--conf", default="~/.glacier-cmd",
        help="Specify config file", metavar="FILE")
    conf_parser.add_argument('-p','--printtostdout', action='store_true',
        help='Print all log messages to stdout')

    args, remaining_argv = conf_parser.parse_known_args()

    # Here we parse config from files in home folder or in current folder
    # We use separate sections for aws and glacier specific configs
    aws = glacier = {}
    config = ConfigParser.SafeConfigParser()
    if config.read(['/etc/glacier-cmd.conf',
                    os.path.expanduser('~/.glacier-cmd'),
                    args.conf]):
        try:
            aws = dict(config.items("aws"))
        except ConfigParser.NoSectionError:
            pass
        try:
            glacier = dict(config.items("glacier"))
        except ConfigParser.NoSectionError:
            pass

    # Join config options with environments
    aws = dict(os.environ.items() + aws.items() )
    glacier = dict(os.environ.items() + glacier.items() )

    # Helper functions
    filt_s= lambda x: x.lower().replace("_","-")
    filt = lambda x,y="": dict(((y+"-" if y not in filt_s(k) else "") +
                             filt_s(k), v) for (k, v) in x.iteritems())
    a_required = lambda x: x not in filt(aws, "aws")
    required = lambda x: x not in filt(glacier)
    a_default = lambda x: filt(aws, "aws").get(x)
    default = lambda x: filt(glacier).get(x)

    # Main configuration parser
    parser = argparse.ArgumentParser(parents=[conf_parser],
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=program_description)
    subparsers = parser.add_subparsers(title='Subcommands',
        help=u"For subcommand help, use: glacier-cmd <subcommand> -h")

    group = parser.add_argument_group('aws')
    help_msg_config = u"(Required if you have not created a \
                        ~/.glacier-cmd or /etc/glacier-cmd.conf config file)"
    group.add_argument('--aws-access-key',
                       required=a_required("aws-access-key"),
                       default=a_default("aws-access-key"),
                       help="Your aws access key " + help_msg_config)
    group.add_argument('--aws-secret-key',
                       required=a_required("aws-secret-key"),
                       default=a_default("aws-secret-key"),
                       help="Your aws secret key " + help_msg_config)
    group = parser.add_argument_group('glacier')
    group.add_argument('--region',
                       required=required("region"),
                       default=default("region"),
                       help="Region where you want to store \
                             your archives " + help_msg_config)
    group.add_argument('--bookkeeping',
                       required=False,
                       default=default("bookkeeping") and True,
                       action="store_true",
                       help="Should we keep book of all created archives.\
                             This requires a Amazon SimpleDB account and its \
                             bookkeeping domain name set")
    group.add_argument('--bookkeeping-domain-name',
                        required=False,
                        default=default("bookkeeping-domain-name"),
                        help="Amazon SimpleDB domain name for bookkeeping.")
    group.add_argument('--logfile',
                       required=False,
                       default=os.path.expanduser('~/.glacier-cmd.log'),
                       help='File to write log messages to.')
    group.add_argument('--loglevel',
                       required=False,
                       default=default('loglevel') if default('loglevel') else 'WARNING',
                       choices=["-1", "DEBUG", "0", "INFO", "1", "WARNING",
                                "2", "ERROR", "3", "CRITICAL"],
                       help="Set the lowest level of messages you want to log.")

    # glacier-cmd mkvault <vault>
    parser_mkvault = subparsers.add_parser("mkvault",
        help="Create a new vault.")
    parser_mkvault.set_defaults(func=mkvault)

    # glacier-cmd lsvault    
    parser_lsvault = subparsers.add_parser("lsvault",
        help="List available vaults.")
    parser_lsvault.set_defaults(func=lsvault)

    # glacier-cmd describevault <vault>
    parser_describevault = subparsers.add_parser('describevault',
        help='Describe a vault.')
    parser_describevault.add_argument('vault',
        help='The vault to be described.')
    parser_describevault.set_defaults(func=describevault)

    # glacier-cmd rmvault <vault>
    parser_rmvault = subparsers.add_parser('rmvault',
        help='Remove a vault.')
    parser_rmvault.add_argument('vault',
        help='The vault to be removed.')
    parser_rmvault.set_defaults(func=rmvault)

    # glacier-cmd upload <vault> <filename> [<description>] [--name <store file name>] [--partsize <part size>]
    # glacier-cmd upload <vault> [<description>] --stdin [--name <store file name>] [--partsize <part size>]
    parser_upload = subparsers.add_parser('upload',
        formatter_class=argparse.RawTextHelpFormatter,
        help='Upload an archive to Amazon Glacier.')
    parser_upload.add_argument('vault',
        help='The vault the archive is to be stored in.')
    parser_upload.add_argument('filename', nargs='?', default=None,
        help='''\
The name of the local file to be uploaded.
May be omitted if --stdin is used.''')
    parser_upload.add_argument('--stdin', action='store_true',
        help='''\
Read data from stdin, instead of local file. 
If enabled, <filename> is ignored and may be omitted.''')
    parser_upload.add_argument('--name', default=None,
        help='''\
Use the given name as the filename for bookkeeping 
purposes. To be used in conjunction with --stdin or 
when the file being uploaded is a temporary file.''')
    parser_upload.add_argument('--partsize', type=int, default=-1,
        help='''\
Part size to use for upload (in MB). Must
be a power of 2 in the range:
    1, 2, 4, 8, ..., 2,048, 4,096.
Values that are not a power of 2 will be
adjusted upwards to the next power of 2.

Amazon accepts up to 10,000 parts per upload.

Smaller parts result in more frequent progress
updates, and less bandwidth wasted if a part
needs to be re-transmitted. On the other hand,
smaller parts limit the size of the archive that
can be uploaded. Some examples:

partsize  MaxArchiveSize
    1        1*1024*1024*10000 ~= 9.7 GB
    4        4*1024*1024*10000 ~= 39 GB
   16       16*1024*1024*10000 ~= 156 GB
  128      128*1024*1024*10000 ~= 1.2 TB
 4096     4096*1024*1024*10000 ~= 39 TB

If not given, the smallest possible part size
will be used when uploading a file, and 128 MB
when uploading from stdin.''')
    parser_upload.add_argument('description', nargs='?', default=None,
        help='Description of the file to be uploaded. Use quotes \
              if your file contains spaces. (optional).')
    parser_upload.set_defaults(func=upload)

    # glacier-cmd listmultiparts <vault>
    parser_listmultiparts = subparsers.add_parser('listmultiparts',
        help='List all active multipart uploads.')
    parser_listmultiparts.add_argument('vault',
        help='The vault to check the active multipart uploads for.')
    parser_listmultiparts.set_defaults(func=listmultiparts)

    # glacier-cmd abortmultipart <vault> <uploadId>
    parser_abortmultipart = subparsers.add_parser('abortmultipart',
        help='Abort a multipart upload.')
    parser_abortmultipart.add_argument('vault',
        help='The vault the upload is for.')
    parser_abortmultipart.add_argument('uploadId',
        help='The id of the upload to be aborted, try listmultiparts.')
    parser_abortmultipart.set_defaults(func=abortmultipart)

    # glacier-cmd inventory <vault> [--refresh]
    parser_inventory = subparsers.add_parser('inventory',
        help='List inventory of a vault, if available. If not available, \
              creates inventory retrieval job if none running already.')
    parser_inventory.add_argument('vault',
        help='The vault to list the inventory of.')
    parser_inventory.add_argument('--refresh', action='store_true',
        help='Create an inventory retrieval job, even if inventory is \
              available or with another retrieval job running.')
    parser_inventory.set_defaults(func=inventory)

    # glacier-cmd getarchive <vault> <archive>
    parser_getarchive = subparsers.add_parser('getarchive',
        help='Requests to make an archive available for download.')
    parser_getarchive.add_argument('vault',
        help='The vault the archive is stored in.')
    parser_getarchive.add_argument('archive',
        help='The archive id.')
##    parser_getarchive.add_argument('--outfile', nargs='?',
##        help='Local file name to store the file. \
##              If omitted data is sent to stdout.')
    parser_getarchive.set_defaults(func=getarchive)

    # glacier-cmd download <vault> <archive> [--outfile <file name>]
    parser_download = subparsers.add_parser('download',
        help='Download a file by archive id.')
    parser_download.add_argument('vault',
        help="Specify the vault in which archive is located.")
    parser_download.add_argument('archive',
        help='The archive to be downloaded.')
    parser_download.add_argument('--outfile',
        help='The name of the local file to store the archive. \
              If omitted, stdout will be used.')
    parser_download.add_argument('--overwrite', action='store_true',
        help='Overwrite an existing local file if one exists when \
              downloading an archive.')
    parser_download.set_defaults(func=download)

    # glacier-cmd rmarchive <vault> <archive>
    parser_rmarchive = subparsers.add_parser('rmarchive',
        help='Remove archive from Amazon Glacier.')
    parser_rmarchive.add_argument('vault',
        help='The vault the archive is stored in.')
    parser_rmarchive.add_argument('archive',
        help='The archive id of the archive to be removed.')
    parser_rmarchive.set_defaults(func=rmarchive)

    # glacier-cmd search [<vault>] [--filename <file name>] [--searchterm <search term>]
    parser_search = subparsers.add_parser('search',
        help='Search Amazon SimpleDB database for available archives \
              (requires bookkeeping to be enabled).')
    parser_search.add_argument('vault', nargs='?', default=None,
        help='The vault to search in. Searching all if omitted.')
    parser_search.add_argument('--filename',
        help='Search key for searching by (part of) file names.')
    parser_search.add_argument('--searchterm',
        help='Search key for searching (part of) description fields.')
    parser_search.set_defaults(func=search)

    # glacier-cmd listjobs <vault>
    parser_listjobs = subparsers.add_parser('listjobs',
        help='List active jobs in a vault.')
    parser_listjobs.add_argument('vault',
        help='The vault to list the jobs for.')
    parser_listjobs.set_defaults(func=listjobs)

    # glacier-cmd describejob <vault>
    parser_describejob = subparsers.add_parser('describejob',
        help='Describe a job.')
    parser_describejob.add_argument('vault',
        help='The vault the job is listed for.')
    parser_describejob.add_argument('jobid',
        help='The job ID of the job to be described.')
    parser_describejob.set_defaults(func=describejob)

    # Process the remaining arguments.
    args = parser.parse_args(remaining_argv)

##    # Set up the logging function.
##    setuplogging(args)

    # Run the subcommand.
    args.func(args)

if __name__ == "__main__":
    sys.exit(main())
