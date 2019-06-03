import urllib, urllib2, json, ssl
import datetime, sys, getpass, argparse, os, socket

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
    portalHost = ''
    adminUsername = ''
    adminPassword = ''
    outputDir = ''
    token = ''
    parser = argparse.ArgumentParser(description='Portal for ArcGIS Security Scanner')
    parser.add_argument('-n', '--hostname', help='Portal hostname')
    parser.add_argument('-u', '--username', help='Admin username')
    parser.add_argument('-p', '--password', help='Admin password')
    parser.add_argument('-o', '--outputdir', help='Output directory')
    parser.add_argument('-t', '--token', help='Portal token')
    parser.add_argument('-?', action='help')
    args=parser.parse_args()

    # Prompt for server hostname if not added as an argument
    if args.hostname:
        portalHost = args.hostname
    else:
        portalHost = raw_input('Enter Portal for ArcGIS fully qualified domain name [' + currentHost + ']: ')
        if portalHost == '':
            portalHost = currentHost

    # Prompt for admin username if not added as an argument
    if args.username:
        adminUsername = args.username
    elif not args.username and not args.token:
        adminUsername = raw_input('Enter administrator username: ')

    # Prompt for admin password if not added as an argument
    if args.password:
        adminPassword = args.password
    elif not args.password and not args.token:
        adminPassword = getpass.getpass(prompt='Enter administrator password: ')

    # Prompt for output directory if not added as an argument
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
    defineScanInfo(portalHost)
    portalUrl = 'https://' + portalHost + ':7443/arcgis'
    if token == '':
        token = generateToken(adminUsername,adminPassword,portalHost,portalUrl)
    portalVer = checkToken(portalUrl,token)
    checkProxy(portalUrl,token,scanResults)
    checkTokenReq(portalUrl + '/sharing/rest/generateToken',scanResults)
    checkServicesDir(portalUrl,token,scanResults)
    checkPortalSelf(portalUrl,token,scanResults)
    checkLDAPS(portalUrl,token,scanResults)
    checkSSL(portalUrl,token,scanResults)
    addHelpLinks(portalHost,scanResults)
    scanReportHTML(portalHost,portalVer,scanResults,outputDir)

# Function to generate token
def generateToken(username,password,portalHost,portalUrl):
    params = {'username':username,
              'password':password,
              'referer':portalUrl,
              'f':'json'}
    try:
        request = urllib2.Request(portalUrl + '/sharing/rest/generateToken', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        genToken = json.loads(response.read())
        if 'token' in genToken.keys():
            return genToken.get('token')
        else:
            print('\nInvalid administrator username or password')
            sys.exit(1)
    except Exception:
        print('Unable to access Portal for ArcGIS on {}'.format(portalHost))
        print(traceback.format_exc())
        sys.exit(1)

# Function to check the portal token and return the portal version if valid
def checkToken(portalUrl,token):
    if token == 'Failed':
        print('\nInvalid administrator username or password')
        sys.exit(0)
    try:
        request = urllib2.Request(portalUrl + '/portaladmin/?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        adminInfo = json.loads(response.read())
        if 'version' in adminInfo.keys():
            return str(adminInfo['version'])
        else:
            print('\nThe user or token provided does not have administrative privileges')
            print('Unable to complete the scan')
            sys.exit(0)
    except Exception:
        print(traceback.format_exc())
        sys.exit(0)

# Check if proxy restrictions are defined
def checkProxy(portalUrl,token,scanResults):
    try:
        request = urllib2.Request(portalUrl + '/portaladmin/security/config?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        secConfig = json.loads(response.read())
        if 'error' in secConfig.keys():
            print('Error checking Portal proxy restrictions')
        elif not 'allowedProxyHosts' in secConfig.keys():
            scanResults.append({'id':'PS01','level':'Critical','test':'Proxy restrictions','result':scanInfo['PS01']})
    except:
        print('Error checking Portal proxy restrictions')
        print(traceback.format_exc())

# Check if credentials in the query paramter are allowed for token requests (GET or POST)
def checkTokenReq(tokenUrl,scanResults):
    try:
        request = urllib2.Request(tokenUrl + '?username=test&password=test&f=json')
        response = urllib2.urlopen(request)
        tokenResponse = json.loads(response.read())
        if ('error' in tokenResponse.keys() and tokenResponse['error']['code'] != 405) or ('token' in tokenResponse.keys()):
            scanResults.append({'id':'PS02','level':'Critical','test':'Token requests','result':tokenUrl + '<br>' + scanInfo['PS02']})
            return
        params = {'client':'requestip','f':'json'}
        request = urllib2.Request(tokenUrl + '?username=test&password=test', urllib.urlencode(params))
        response = urllib2.urlopen(request)
        tokenResponse = json.loads(response.read())
        if 'error' in tokenResponse.keys():
            if (tokenResponse['error']['code'] == 400) and 'POST' not in unicode(tokenResponse['error']['details']):
                scanResults.append({'id': 'PS02', 'level': 'Critical', 'test': 'Token requests', 'result': tokenUrl + '<br>' + scanInfo['PS02']})
        else:
            scanResults.append({'id': 'PS02', 'level': 'Critical', 'test': 'Token requests', 'result': tokenUrl + '<br>' + scanInfo['PS02']})
    except:
        print('Error checking token requests - {}'.format(tokenUrl))
        print(traceback.format_exc())

# Check if the HTML access to the portal sharing directory is disabled
def checkServicesDir(portalUrl,token,scanResults):
    try:
        request = urllib2.Request(portalUrl + '/portaladmin/security/config?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        secConfig = json.loads(response.read())
        if 'error' in secConfig.keys():
            print('Error checking Portal services directory')
        elif 'disableServicesDirectory' in secConfig.keys():
            if not secConfig.get('disableServicesDirectory'):
                scanResults.append({'id':'PS03','level':'Important','test':'Portal services directory','result':scanInfo['PS03']})
        else:
            print('Error checking Portal services directory')
    except:
        print('Error checking Portal services directory')
        print(traceback.format_exc())

# Check if Portal is limited to HTTPS only, if sign-up is disabled, and is anonymous access is allowed
def checkPortalSelf(portalUrl,token,scanResults):
    try:
        request = urllib2.Request(portalUrl + '/sharing/rest/portals/self?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        portalSelf = json.loads(response.read())
        if 'error' in portalSelf.keys():
            raise Exception
        if 'allSSL' in portalSelf.keys():
            if str(portalSelf.get('allSSL')) == 'false':
                scanResults.append({'id':'PS04','level':'Important','test':'Web communication','result':scanInfo['PS04']})
        else:
            print('Error checking Portal HTTPS properties')
        if 'disableSignup' in portalSelf.keys():
            if not portalSelf.get('disableSignup'):
                scanResults.append({'id':'PS05','level':'Recommended','test':'Built-in account sign-up','result':scanInfo['PS05']})
        else:
            print('Error checking Portal signup properties')
        if 'access' in portalSelf.keys():
            if str(portalSelf.get('access')) == 'public':
                scanResults.append({'id':'PS06','level':'Recommended','test':'Anonymous access','result':scanInfo['PS06']})
        else:
            print('Error checking for anonymous access')
        if 'allowedOrigins' in portalSelf.keys():
            if str(portalSelf['allowedOrigins']) == '[]':
                scanResults.append({'id':'PS09','level':'Recommended','test':'Cross-domain requests','result':scanInfo['PS09']})
        else:
            print('Error checking for cross-domain restrictions')
    except:
        print('Error checking Portal properties')
        print(traceback.format_exc())

# Check if user/group store configuration is using LDAP and if so, is it LDAPS
def checkLDAPS(portalUrl, token, scanResults):
    try:
        request = urllib2.Request(portalUrl + '/portaladmin/security/config?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        secConfig = json.loads(response.read())
        if not 'userStoreConfig' in secConfig.keys() or not 'groupStoreConfig' in secConfig.keys():
            raise KeyError('Missing key in config')
        if secConfig['userStoreConfig']['type'] == 'LDAP':
            if secConfig['userStoreConfig']['properties']['ldapURLForUsers'].split(':')[0].lower() == 'ldap':
                scanResults.append({'id':'PS07', 'level':'Recommended','test':'LDAP identity store','result':scanInfo['PS07']})
                return
        if secConfig['groupStoreConfig']['type'] == 'LDAP':
            if secConfig['groupStoreConfig']['properties']['ldapURLForUsers'].split(':')[0].lower() == 'ldap' or secConfig['groupStoreConfig']['properties']['ldapURLForRoles'].split(':')[0].lower() == 'ldap':

                scanResults.append({'id': 'PS07', 'level': 'Recommended', 'test': 'LDAP identity store','result':scanInfo['PS07']})
                return
    except:
        print('Error checking user/group store configuration')
        print(traceback.format_exc())

# Check if the SSL certificate bound to 7443 is CA-signed or self-signed
def checkSSL(portalUrl, token, scanResults):
    try:
        request = urllib2.Request(portalUrl + '/portaladmin/security/sslCertificates?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        sslConfig = json.loads(response.read())
        if not 'webServerCertificateAlias' in sslConfig.keys():
            raise Exception
        request = urllib2.Request(portalUrl + '/portaladmin/security/sslCertificates/' + sslConfig['webServerCertificateAlias'] + '?token=' + token + '&f=json')
        request.add_header('Referer', portalUrl)
        response = urllib2.urlopen(request)
        ptlCertificate = json.loads(response.read())
        if 'Issuer' in ptlCertificate.keys() and 'Owner' in ptlCertificate.keys() and ptlCertificate['Issuer'] == ptlCertificate['Owner']:
            scanResults.append({'id': 'PS08', 'level': 'Recommended', 'test': 'Portal SSL certificate', 'result': scanInfo['PS08']})
        elif 'issuer' in ptlCertificate.keys() and 'subject' in ptlCertificate.keys() and ptlCertificate['issuer'] == ptlCertificate['subject']:
            scanResults.append({'id': 'PS08', 'level': 'Recommended', 'test': 'Portal SSL certificate', 'result': scanInfo['PS08']})
    except:
        print('Error checking SSL certificate configuration')
        print(traceback.format_exc())

# Output scan results to HTML format
def scanReportHTML(portalHost,portalVer,scanResults,outputDir):
    outputFile = os.path.join(outputDir, 'portalScanReport_' + portalHost.split('.')[0] + '_' + str(datetime.datetime.now().date()) + '.html')
    try:
        with open(outputFile, 'w') as htmlOut:
            htmlOut.write('<html><body>\n')
            htmlOut.write('<h1>Portal for ArcGIS Security Scan Report - ' + datetime.date.today().strftime('%x') + '</h1>\n')
            htmlOut.write('<h2>' + portalHost + ' (' + portalVer + ')</h2>\n')
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
        print(traceback.format_exc())
        sys.exit(2)
    print('\nPortal scan completed - {} security items noted'.format(len(scanResults)))
    print('Scan results written to {}'.format(outputFile))

# Function to define scan result information
def defineScanInfo(portalHost):
    global scanInfo
    scanInfo = {
        'PS01': 'The portal proxy capability is unrestricted. This should be limited to trusted web addresses.',
        'PS02': 'Token requests with credentials in the query parameter are supported. When generating tokens, a user\'s '
                'credentials could be provided as part of the url and may be exposed through browser history or in network '
                'logs. This should be disabled unless required by other applications.',
        'PS03': 'The portal services directory is accessible through a web browser. This should be disabled to reduce the '
                'chances that your portal items, services, web maps, groups, and other resources can be browsed, found '
                'in a web search, or queried through HTML forms.',
        'PS04': 'To prevent the interception of any communication within the portal, it is recommended that you configure '
                'your portal and the web server hosting the Web Adaptor to enforce HTTPS.',
        'PS05': 'By default, users can click the Create An Account button on the portal sign-up page to create a built-in portal '
                'account. If you are using enterprise accounts or you want to create all accounts manually, this option should be disabled.',
        'PS06': 'To prevent any user from accessing content without first providing credentials to the portal, it is recommended '
                'that you configure your portal to disable anonymous access.',
        'PS07': 'To ensure encrypted communication between your portal and the LDAP identity provider, it is recommended '
                'that you use LDAPS in the ldapURLForUsers and ldapURLForRoles properties listed in the user store and '
                'group store configuration parameters.',
        'PS08': 'To help reduce web browser warnings or other unexpected behavior from clients communicating with your '
                'portal, it is recommended to import and use a CA-signed SSL certificate bound to port 7443.',
        'PS09': 'Cross-domain requests are unrestricted. To reduce the possibility of an unknown application '
                'accessing a shared portal item, it is recommended to restrict cross-domain requests '
                'to applications hosted only in domains that you trust.'}

# Function to add help links to the scan results
def addHelpLinks(portalHost,scanResults):
    helpIds = {
        'PS01':'120001146',
        'PS03':'120001147',
        'PS04':'120001148',
        'PS05':'120001149',
        'PS06':'120001150',
        'PS07':'120001265',
        'PS08':'120001264',
        'PS09':'120001289'}
    helpBase = 'http://' + portalHost + ':7080/arcgis/portalhelp/en/admin/help/'
    request = urllib2.Request('http://' + portalHost + ':7080/arcgis/portalhelp/en/admin/help/cxhelp.js')
    response = urllib2.urlopen(request)
    helpLinks = json.loads(response.read())
    for scan in scanResults:
        if scan['id'] in helpIds.keys() and 'm' in helpLinks.keys():
            if helpIds[scan['id']] in helpLinks['m'].keys():
                scan['result'] += ' <a href="' + helpBase + helpLinks['m'][helpIds[scan['id']]] + '" target="_blank">More information</a>'

# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))