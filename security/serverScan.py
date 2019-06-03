import urllib, urllib2, json, ssl
import sys, datetime, getpass, argparse, os, socket

# Defines the entry point into the script
def main(argv):

    # disable ssl certificate validation
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    currentHost = unicode(socket.getfqdn()).lower()
    currentDir = os.getcwd()
    serverHost = ''
    adminUsername = ''
    adminPassword = ''
    outputDir = ''
    token = ''
    parser = argparse.ArgumentParser(description='ArcGIS Server Security Scanner')
    parser.add_argument('-n', '--hostname', help='Server hostname')
    parser.add_argument('-u', '--username', help='Admin username')
    parser.add_argument('-p', '--password', help='Admin password')
    parser.add_argument('-o', '--outputdir', help='Output directory')
    parser.add_argument('-t', '--token', help='Server token')
    parser.add_argument('-?', action='help')
    args=parser.parse_args()

    # Prompt for server hostname if not included as an argument
    if args.hostname:
        serverHost = args.hostname
    else:
        serverHost = raw_input('Enter ArcGIS Server fully qualified domain name [' + currentHost + ']: ')
        if serverHost == '':
            serverHost = currentHost

    # Prompt for admin username if not included as an argument
    if args.username:
        adminUsername = args.username
    elif not args.username and not args.token:
        adminUsername = raw_input('Enter administrator username: ')

    # Prompt for admin password if not included as an argument
    if args.password:
        adminPassword = args.password
    elif not args.password and not args.token:
        adminPassword = getpass.getpass(prompt='Enter administrator password: ')

    # Prompt for output directory if not included as an argument
    if args.outputdir:
        outputDir = args.outputdir
    else:
        outputDir = raw_input('Enter output directory [' + currentDir + ']: ')
        if outputDir == '':
            outputDir = currentDir

    # Define token if added as an argument
    if args.token:
        token = args.token

    scanResults = []
    defineScanInfo(serverHost)
    serverUrl = checkHTTPS(serverHost,scanResults)
    serverVer,portalUrl = serverInfo(serverUrl)
    if token == '':
        token = generateToken(adminUsername,adminPassword,serverUrl)
    checkToken(serverUrl,token,portalUrl)
    checkStdQry(serverUrl,token,scanResults)
    checkTokenReq(serverUrl + '/tokens/generateToken',scanResults)
    checkRest(serverUrl,token,scanResults)
    checkPSA(serverUrl,token,scanResults)
    checkSystem(serverUrl,token,scanResults)
    checkWA(serverUrl,token,scanResults)
    checkLDAPS(serverUrl,token,scanResults)
    checkSSL(serverUrl,serverHost,token,scanResults)
    serviceList = getServices(serverUrl,token)
    checkServices(serverUrl,token,serviceList,portalUrl,scanResults)
    addHelpLinks(serverHost,scanResults)
    scanReportHTML(serverHost,serverVer,scanResults,outputDir)

# Function to generate token
def generateToken(username,password,serverUrl):
    params = {'username':username,
              'password':password,
              'client':'requestip',
              'f':'json'}
    try:
        tokenUrl = serverUrl + '/admin/generateToken'
        request = urllib2.Request(tokenUrl, urllib.urlencode(params))
        response = urllib2.urlopen(request)
        genToken = json.loads(response.read())
        if 'token' in genToken.keys():
            return genToken.get('token')
        else:
            return 'Failed'
    except Exception, e:
        print('Unable to generate token - {}'.format(e))
        sys.exit(0)

# Check if Server if federated with a Portal
def serverInfo(serverUrl):
    try:
        request = urllib2.Request(serverUrl + '/rest/info?f=json')
        response = urllib2.urlopen(request)
        restInfo = json.loads(response.read())
        if 'owningSystemUrl' in restInfo.keys():
            portalUrl = restInfo['owningSystemUrl']
        else:
            portalUrl = ''
        serverVer = str(restInfo['fullVersion'])
        return serverVer,portalUrl
    except:
        print('Error checking server information')
        sys.exit(1)

# Check if HTTP and/or HTTPS is supported
def checkHTTPS(hostname,scanResults):
    try:
        request = urllib2.Request('http://' + hostname + ':6080/arcgis/admin/generateToken?f=json')
        response = urllib2.urlopen(request)
        sslInfo = json.loads(response.read())
        if 'ssl' in sslInfo.keys():
            https = sslInfo['ssl']['supportsSSL']
            if (https):
                serverUrl = 'https://' + hostname + ':6443/arcgis'
            else:
                serverUrl = 'http://' + hostname + ':6080/arcgis'
                scanResults.append({'id':'SS01','level':'Critical','test':'Web communication','result':scanInfo['SS01']})
            return serverUrl
        else:
            sys.exit(0)
    except:
        print('Error accessing ArcGIS for Server on {}'.format(hostname))
        sys.exit(0)

# Check if token is valid
def checkToken(serverUrl,token,portalUrl):
    if token == 'Failed':
        print('\n** Invalid administrator username or password **')
        if portalUrl != '':
            print('\nThis server is currently federated with Portal for ArcGIS.')
            print('You can use the ArcGIS Server primary site administrator account to run ')
            print('this script or provide a token acquired from Portal.  If the ArGIS Server ')
            print('primary site account has been disabled, a Portal token must be used.\n\n')
            print('A Portal token can be acquired from the following url:')
            print ('{}/sharing/rest/generateToken\n\n'.format(portalUrl))
            print('You can then run this script using -t option to specify the token.\n')
            print('serverScan.py -t <Portal token>')
        sys.exit(0)
    try:
        params = {'token': token}
        request = urllib2.Request(serverUrl + '/admin/info?f=json', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        adminInfo = json.loads(response.read())
        if 'loggedInUserPrivilege' in adminInfo.keys() and adminInfo['loggedInUserPrivilege'] == 'ADMINISTER':
            return
        elif 'loggedInUserPrivilege' in adminInfo.keys() and adminInfo['loggedInUserPrivilege'] != 'ADMINISTER':
            print('\nThe user or token provided does not have administrative privileges')
            print('Unable to complete the scan')
            sys.exit(0)
        else:
            print('\nInvalid token provided to access ArcGIS Server')
            sys.exit(0)
    except:
        sys.exit(0)

# Check if standardized queries are enabled
def checkStdQry(serverUrl,token,scanResults):
    try:
        params = {'token':token}
        request = urllib2.Request(serverUrl + '/admin/system/properties?f=json', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        sysProps = json.loads(response.read())
        if 'standardizedQueries' in sysProps.keys():
            if str(sysProps.get('standardizedQueries')).lower() == 'false':
                scanResults.append({'id':'SS02','level':'Critical','test':'Standardized queries','result':scanInfo['SS02']})
    except:
        print('Error checking Server system properties')

# Check if GET requests and POST requests with credentials as query paramter are allowed for token requests
def checkTokenReq(tokenUrl,scanResults):
    try:
        request = urllib2.Request(tokenUrl + '?username=test&password=test&f=json')
        response = urllib2.urlopen(request)
        tokenResponse = json.loads(response.read())
        if ('error' in tokenResponse.keys() and tokenResponse['error']['code'] != 405) or ('token' in tokenResponse.keys()):
            scanResults.append({'id':'SS03','level':'Critical','test':'Token requests','result':tokenUrl + '<br>' + scanInfo['SS03']})
            return
        params = {'client':'requestip','f':'json'}
        request = urllib2.Request(tokenUrl + '?username=test&password=test', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        tokenResponse = json.loads(response.read())
        if ('error' in tokenResponse.keys() and tokenResponse['error']['code'] != 405) or ('token' in tokenResponse.keys()):
            scanResults.append({'id':'SS04','level':'Critical','test':'Token requests','result':tokenUrl + '<br>' + scanInfo['SS04']})
    except:
        print('Error checking token requests - {}'.format(tokenUrl))

# Check if services directory is disabled and restrictions on cross-domain requests
def checkRest(serverUrl,token,scanResults):
    try:
        params = {'token':token,'f':'json'}
        request = urllib2.Request(serverUrl + '/admin/system/handlers/rest/servicesdirectory', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        restProps = json.loads(response.read())
        if str(restProps['enabled']).lower() == 'true':
            scanResults.append({'id':'SS07','level':'Important','test':'Rest services directory','result':scanInfo['SS07']})
        if restProps['allowedOrigins'] == '*':
            scanResults.append({'id':'SS08','level':'Important','test':'Cross-domain requests','result':scanInfo['SS08']})
    except:
        print('Error checking services directory properties')

# Check if PSA account is disabled
def checkPSA(serverUrl,token,scanResults):
    try:
        params = {'token':token,'f':'json'}
        request = urllib2.Request(serverUrl + '/admin/security/psa', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        psaProps = json.loads(response.read())
        if str(psaProps['disabled']).lower() == 'false':
            scanResults.append({'id':'SS11','level':'Recommended','test':'PSA account status','result':scanInfo['SS11']})
    except:
        print('Error obtaining PSA account status')

# Check if System folder has any permissions assigned to it
def checkSystem(serverUrl,token,scanResults):
    try:
        params = {'token':token,'f':'json'}
        request = urllib2.Request(serverUrl + '/admin/services/System/permissions', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        sysPerm = json.loads(response.read())
        if not sysPerm.get('permissions') == []:
            accessList = []
            for users in sysPerm['permissions']:
                accessList.append(str(users['principal']))
            scanResults.append({'id':'SS06','level':'Critical','test':'System folder permissions','result':'Open to roles: ' + ', '.join(str(user) for user in accessList) + '<br>' + scanInfo['SS06']})
    except:
        print('Error accessing System folder permissions')

# Check if web adaptor is registered over HTTPS
def checkWA(serverUrl,token,scanResults):
    try:
        params = {'token':token,'f':'json'}
        request = urllib2.Request(serverUrl + '/admin/system/webadaptors', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        waProps = json.loads(response.read())
        if 'webAdaptors' in waProps.keys():
            for wa in waProps['webAdaptors']:
                if wa['httpPort'] != -1:
                    scanResults.append({'id':'SS10','level':'Recommended','test':'Web adaptor registration','result':scanInfo['SS10']})
                    break
        else:
            print('Error accessing web adaptor information')
    except:
        print('Error accessing web adaptor information')

# Check if user/group store configuration is using LDAP and if so, is it LDAPS
def checkLDAPS(serverUrl, token, scanResults):
    try:
        request = urllib2.Request(serverUrl + '/admin/security/config?token=' + token + '&f=json')
        response = urllib2.urlopen(request)
        secConfig = json.loads(response.read())
        if not 'userStoreConfig' in secConfig.keys() or not 'roleStoreConfig' in secConfig.keys():
            raise KeyError('Missing key in config')
        if secConfig['userStoreConfig']['type'] == 'LDAP':
            if secConfig['userStoreConfig']['properties']['ldapURLForUsers'].split(':')[0].lower() == 'ldap':
                scanResults.append({'id': 'SS13', 'level': 'Recommended', 'test': 'LDAP identity store', 'result': scanInfo['SS13']})
                return
        if secConfig['roleStoreConfig']['type'] == 'LDAP':
            if secConfig['roleStoreConfig']['properties']['ldapURLForUsers'].split(':')[0].lower() == 'ldap' or secConfig['roleStoreConfig']['properties']['ldapURLForRoles'].split(':')[0].lower() == 'ldap':
                scanResults.append({'id': 'SS13', 'level': 'Recommended', 'test': 'LDAP identity store', 'result': scanInfo['SS13']})
                return
    except:
        print('Error checking user/group store configuration')

# Check if the SSL certificate bound to 6443 is CA-signed or self-signed
def checkSSL(serverUrl, serverHost, token, scanResults):
    try:
        request = urllib2.Request(serverUrl + '/admin/machines/' + serverHost.upper() + '?token=' + token + '&f=json')
        response = urllib2.urlopen(request)
        sslConfig = json.loads(response.read())
        if not 'webServerCertificateAlias' in sslConfig.keys():
            raise KeyError('Missing key in config')
        request = urllib2.Request(serverUrl + '/admin/machines/' + serverHost.upper() + '/sslCertificates/' +
            sslConfig['webServerCertificateAlias'] + '?token=' + token + '&f=json')
        response = urllib2.urlopen(request)
        svrCertificate = json.loads(response.read())
        if 'Issuer' in svrCertificate.keys() and 'Owner' in svrCertificate.keys() and svrCertificate['Issuer'] == svrCertificate['Owner']:
            scanResults.append({'id': 'SS14', 'level': 'Recommended', 'test': 'Server SSL certificate', 'result': scanInfo['SS14']})
        elif 'issuer' in svrCertificate.keys() and 'subject' in svrCertificate.keys() and svrCertificate['issuer'] == svrCertificate['subject']:
            scanResults.append({'id': 'SS14', 'level': 'Recommended', 'test': 'Server SSL certificate', 'result': scanInfo['SS14']})
    except:
        print('Error checking SSL certificate configuration')

# Generate list of map services in all folders pulled from the admin/services page
def getServices(serverUrl,token):
    serviceList = []
    try:
        params = {'token':token,'f':'json'}
        request = urllib2.Request(serverUrl + '/admin/services', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        restRoot = json.loads(response.read())
        # Return services in root folder
        for services in restRoot['services']:
            if services['type'] == 'MapServer' or services['type'] == 'FeatureServer':
                serviceList.append({'name':services['serviceName'],'type':services['type']})
        # Return services in subfolders
        for folder in restRoot['folders']:
            params = {'token':token,'f':'json'}
            request = urllib2.Request(serverUrl + '/admin/services/' + folder, urllib.urlencode(params))
            response = urllib2.urlopen(request)
            for services in json.loads(response.read())['services']:
                if services['type'] == 'MapServer' or services['type'] == 'FeatureServer':
                    serviceList.append({'name':services['folderName'] + '/' + services['serviceName'],'type':services['type']})
        return serviceList
    except:
        return 'Error'

# Check properties and capabilities for each map and feature service in the list
def checkServices(serverUrl,token,serviceList,portalUrl,scanResults):
    isFederated = (portalUrl != '')
    try:
        for service in serviceList:
            params = {'token':token,'f':'json'}
            request = urllib2.Request(serverUrl + '/admin/services/' + urllib.quote(service['name'].encode('utf-8')) + '.' + service['type'], urllib.urlencode(params))
            response = urllib2.urlopen(request)
            svcParams = json.loads(response.read())
            if service['type'] == 'MapServer':
                if 'extensions' in svcParams.keys():
                    for ext in svcParams['extensions']:
                        if ext['typeName'] == 'FeatureServer' and ext['enabled'] == 'true':
                            if (ext['properties']['xssPreventionEnabled']).lower() == 'false':
                                scanResults.append({'id': 'SS05', 'level': 'Critical', 'test': 'Web content filtering', 'result': 'Feature service: ' + service['name'] + '<br>' + scanInfo['SS05']})
                            featureOps = ext['capabilities'].split(',')
                            if 'Delete' in featureOps or 'Update' in featureOps:
                                featurePerm = checkPerm(serverUrl, token, service['name'], isFederated)
                                if featurePerm == 'Open':
                                    scanResults.append({'id': 'SS12', 'level': 'Recommended', 'test': 'Feature service operations', 'result': 'Feature service: ' + service['name'] + '<br>' + scanInfo['SS12']})
                if 'properties' in svcParams.keys() and 'enableDynamicLayers' in svcParams['properties'].keys() and 'dynamicDataWorkspaces' in svcParams['properties'].keys():
                    if (svcParams['properties']['enableDynamicLayers']).lower() == 'true' and svcParams['properties']['dynamicDataWorkspaces'] not in ('[]',''):
                        scanResults.append({'id': 'SS09', 'level': 'Important', 'test': 'Dynamic workspace', 'result': 'Map service: ' + service['name'] + '<br>' + scanInfo['SS09']})
            elif service['type'] == 'FeatureServer':
                if 'jsonProperties' in svcParams.keys() and 'xssPreventionInfo' in svcParams['jsonProperties'].keys():
                    if not svcParams['jsonProperties']['xssPreventionInfo']['xssPreventionEnabled']:
                        scanResults.append({'id': 'SS05', 'level': 'Critical', 'test': 'Web content filtering', 'result': 'Feature service: ' + service['name'] + '<br>' + scanInfo['SS05']})
                if 'capabilities' in svcParams.keys():
                    featureOps = svcParams['capabilities'].split(',')
                    if 'Delete' in featureOps or 'Update' in featureOps:
                        featurePerm = checkPerm(serverUrl, token, service['name'], isFederated)
                        if featurePerm == 'Open':
                            scanResults.append({'id': 'SS12', 'level': 'Recommended', 'test': 'Feature service operations', 'result': 'Feature service: ' + service['name'] + '<br>' + scanInfo['SS12']})
    except:
        print('Error checking service properties')

# Check permissions on a service - return 'Open' if not secured
def checkPerm(serverUrl, token, service, federated):
    try:
        if not federated:
            params = {'token':token,'f':'json'}
            request = urllib2.Request(serverUrl + '/admin/services/' + service + '.MapServer/permissions', urllib.urlencode(params))
            response = urllib2.urlopen(request)
            svcPerm = json.loads(response.read())
            if 'permissions' in svcPerm.keys():
                for principal in svcPerm['permissions']:
                    if principal['principal'] == 'esriEveryone':
                        return 'Open'
                return 'Secured'
            else:
                return 'Error'
        else:
            request = urllib2.Request(serverUrl + '/rest/services/' + service + '/FeatureServer?f=json')
            response = urllib2.urlopen(request)
            svcInfo = json.loads(response.read())
            if 'currentVersion' in svcInfo.keys():
                return 'Open'
            else:
                return 'Secured'
    except:
        return 'Error'

# Output scan results to HTML format
def scanReportHTML(serverHost,serverVer,scanResults,outputDir):
    outputFile = os.path.join(outputDir, 'serverScanReport_' + serverHost.split('.')[0] + '_' + str(datetime.datetime.now().date()) + '.html')
    try:
        with open(outputFile, 'w') as htmlOut:
            htmlOut.write('<html><body>\n')
            htmlOut.write('<h1>ArcGIS Server Security Scan Report - ' + datetime.date.today().strftime('%x') + '</h1>\n')
            htmlOut.write('<h2>' + serverHost + ' (' + serverVer + ')</h2>\n')
            if len(scanResults) == 0:
                htmlOut.write('<h3>No security items were discovered that need to be reviewed.</h3>\n')
                htmlOut.write('</body></html>')
            else:
                htmlOut.write('<h3>Potential security items to review</h3>\n')
                htmlOut.write('<table cellpadding="5">\n')
                htmlOut.write('<tr><th align="left"><u>Id</u></th>'
                              '<th align="left"><u>Severity</u></th>'
                              '<th align="left"><u>Property Tested</u></th>'
                              '<th align="left"><u>Scan Results</u></th></tr>\n')
                for scan in sorted(scanResults, key=lambda x:(x['level'],x['test'])):
                    htmlOut.write('<tr valign="top"><td width="5%">' + scan['id'] + '</td>'
                                  '<td width="10%">' + scan['level'] + '</td>'
                                  '<td width="15%">' + scan['test'] + '</td>'
                                  '<td width="70%">' + scan['result'] + '</td></tr>\n')
                htmlOut.write('</table></body></html>')
            htmlOut.close()
    except:
        print('Unable to write to {}'.format(outputDir))
        print('Update permissions or specify an alternate output directory')
        sys.exit(2)
    print('\nServer scan completed - {} security items noted'.format(len(scanResults)))
    print('Scan results written to {}'.format(outputFile))

# Function to define scan result information
def defineScanInfo(serverHost):
    global scanInfo
    scanInfo = {
        'SS01': 'HTTPS is not enabled for ArcGIS Server. To prevent the interception of any communication, it is '
                'recommended that you configure ArcGIS Server and ArcGIS Web Adaptor (if installed) to enforce SSL encryption.',
        'SS02': 'Enforcing standardized queries is disabled. To provide protection against SQL injection attacks, it is '
                'critical that this option be enabled.',
        'SS03': 'Generate token requests via GET are supported.  When generating tokens via GET, a user\'s credentials '
                'are sent as part of the url and can be captured and exposed through browser history or network logs. This should be '
                'disabled unless required by other applications.',
        'SS04': 'Generate token requests via POST with credentials in the query parameter are supported. When generating tokens, a '
                'user\'s credentials could be provided as part of the url and may be exposed through browser history or in network '
                'logs. This should be disabled unless required by other applications.',
        'SS05': 'The filter web content property for this feature service is disabled.  This allows a user to enter any text '
                'into the input fields and exposes it to potential cross-site scripting (XSS) attacks.  Unless unsupported '
                'HTML entities or attributes are required, this property should be enabled.',
        'SS06': 'Non-default permissions are applied to the System folder in Server Manager. By default, only administrators and '
                'publishers should have access to the services in the System folder.',
        'SS07': 'The Rest services directory is accessible through a web browser. Unless being actively used to search for '
                'and find services by users, this '
                'should be disabled to reduce the chance that your services can be browsed, found in a web search, '
                'or queried through HTML forms. This also provides further protection against cross-site scripting (XSS) attacks.',
        'SS08': 'Cross-domain requests are unrestricted. To reduce the possibility of an unknown application '
                'sending malicious commands to your web services, it is recommended to restrict the use of your services '
                'to applications hosted only in domains that you trust.',
        'SS09': 'One or more dynamic workspaces are registered with this map service.  To prevent a malicious party from obtaining the '
                'workspace ID and potentially gaining access, these dynamic workspaces should be removed.',
        'SS10': 'One or more web adaptors are registered over HTTP. To allow Server Manager to successfully redirect to '
                'HTTPS, all web adaptors should be registered over HTTPS. This requires unregistering the current '
                'web adaptor and registering it again by accessing the web adaptor url over HTTPS.',
        'SS11': 'The primary site administrator account is enabled. It is recommended that you disable this account to '
                'ensure that there is not another way to administer ArcGIS Server other than the group or role '
                'that has been specified in your identity store.',
        'SS12': 'This feature service has the update and/or delete operations enabled and is open to anonymous access.  This '
                'allows the feature service data to be changed and/or deleted without authentication.',
        'SS13': 'To ensure encrypted communication between ArcGIS Server and the LDAP identity provider, it is recommended '
                'that you use ldaps:// in the connection URL defined for both the LDAP User Store and LDAP Role Store '
                'configurations (if used).',
        'SS14': 'To help reduce web browser warnings or other unexpected behavior from clients communicating with ArcGIS '
                'Server, it is recommended to import and use a CA-signed SSL certificate bound to port 6443.'}

# Function to add help links to the scan results
def addHelpLinks(serverHost,scanResults):
    helpIds = {
        'SS01':'120001151',
        'SS02':'120001152',
        'SS03':'120001153',
        'SS04':'120001153',
        'SS05':'120001154',
        'SS06':'120000521',
        'SS07':'120001155',
        'SS08':'120001156',
        'SS09':'120000797',
        'SS10':'120001172',
        'SS11':'120001158',
        'SS12':'120001160',
        'SS13':'120001261',
        'SS14':'120001263'}
    helpBase = 'http://' + serverHost + ':6080/arcgis/help/en/'
    request = urllib2.Request('http://' + serverHost + ':6080/arcgis/help/en/cxhelp.js')
    response = urllib2.urlopen(request)
    helpLinks = json.loads(response.read())
    for scan in scanResults:
        if scan['id'] in helpIds.keys() and 'm' in helpLinks.keys():
            if helpIds[scan['id']] in helpLinks['m'].keys():
                scan['result'] += ' <a href="' + helpBase + helpLinks['m'][helpIds[scan['id']]] + '" target="_blank">More information</a>'

# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))