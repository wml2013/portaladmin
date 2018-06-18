# Date:			31/05/2018
# Description:		Changed locallogger so that it passes messages to console only.Requires the LocalLogger Utils. 
#		    	LocalLogger is an Esri bit of code. Check out PortalAdmin_nolocallog.py for a version that writes to a local file.


import os, sys
import json
import importlib.util
from arcgis.gis import GIS
import argparse

from utils import localLogger
from utils.exceptions import *


def _getCertificateAliasName(cert, raiseEx = True):
    if "Alias name" in cert.properties:
        return cert.properties["Alias name"].lower()
    elif "aliasName" in cert.properties:
        return cert.properties["aliasName"].lower()
    elif raiseEx:
        raise ApplicationError("Could not determine certificate alias name")
    else:
        return None

def _checkIfCertificateExists(gis, certName):
    """
    Checks whether the certificate has been registered in the portal and, if so,
    returns the certificate.
    """
    for cert in gis.admin.security.ssl.list():
        compName = _getCertificateAliasName(cert)
        if compName.lower() == certName.lower():
            return cert
    return None

def installSSLCertificate(gis):
    """
    Registering the certificate to be used by the Portal.
    """
    localLogger.write("Working on SSL Certificate")
    localLogger.incIndent()

    try:
        certificateAlias = portal_config.sslCertificates["alias"].lower()
        certToInstall = _checkIfCertificateExists(gis,certificateAlias)
        localLogger.write("Checking if SSL Certificate exists")
        if certToInstall == None:
            localLogger.write("ERROR: Certificate with alias \"{}\" has not been registered".format(certificateAlias))
            return False

        installedCertificateAlias = gis.admin.security.ssl.properties["webServerCertificateAlias"]
        certToInstallAlias = _getCertificateAliasName(certToInstall)

        # Makes changes to existing Protocols and Ciphers regardless of installed certificate
        ssl_protocols = ",".join(portal_config.sslCertificates["ssl_protocols"])
        ssl_ciphers = ", ".join(portal_config.sslCertificates["cipher_suites"])
        localLogger.write("Editing existing SSL Protocols & Cipher Suites")
        gis.admin.security.ssl.update(certToInstallAlias,ssl_protocols, ssl_ciphers)

        if certToInstallAlias != installedCertificateAlias:
            #
            # Install the new certificate
            #
            localLogger.write("Registering certificate with alias \"{}\" as the portal certificate".format(certToInstallAlias))
            #gis.admin.security.ssl.update(certToInstallAlias, portal_config.sslCertificates["ssl_protocols"],portal_config.sslCertificates["cipher_suites"])
            #
            # Now make the changes to Protocols and Ciphers
            #
            ssl_protocols = ",".join(portal_config.sslCertificates["ssl_protocols"])
            ssl_ciphers = ", ".join(portal_config.sslCertificates["cipher_suites"])
            localLogger.write("Editing SSL Protocols & Cipher Suites due to new certificate")
            gis.admin.security.ssl.update(certToInstallAlias,ssl_protocols, ssl_ciphers)
        else:
            localLogger.write("Certificate with alias \"{}\" is already installed as the portal certificate".format(certToInstallAlias))
        return True

    except Exception as ex:
        localLogger.write(FormatExceptions("ERROR: Unexpected exception thrown", ex))
        return False
    finally:
        localLogger.decIndent()

def _findRole(gis, roleName):
    for role in gis.users.roles.all():
        if role.name.lower() == roleName.lower():
            return role
    return None

def configureRoles(gis):
    localLogger.write("Creating roles")
    localLogger.incIndent()

    results = []
    try:
        for configRole in portal_config.roles:
            with localLogger.DisableAPILogging():
                roleExists = gis.users.roles.exists(configRole["name"])

            if not roleExists:
                localLogger.write("Creating role: " + configRole["name"])
                with localLogger.DisableAPILogging():
                    result = gis.users.roles.create(name = configRole["name"],
                                                    description = configRole["description"],
                                                    privileges = configRole["privileges"])
                if result == None:
                    localLogger.write("  Failed to create role")
                    results.append(False)
                else:
                    results.append(True)
            else:
                localLogger.write("Role already exists: " + configRole["name"])
                results.append(True)
        return all(results)
    except Exception as ex:
        localLogger.write(FormatExceptions("ERROR: Unexpected exception thrown", ex))
        return False
    finally:
        localLogger.decIndent()

def disableLivingAtlas(gis):
    localLogger.write("Disabling Living Atlas")
    localLogger.incIndent()

    try:
        with localLogger.DisableAPILogging():
            livingAtlas = gis.admin.living_atlas
            groups = gis.groups.search("owner:esri_livingatlas")
        #
        # Extract the groups we want
        #
        livingAtlasGroup = None
        livingAtlasContentGroup = None
        for grp in groups:
            if grp["title"].lower() == "living atlas" and grp["owner"] == "esri_livingatlas":
                livingAtlasGroup = grp
            elif grp["title"].lower() == "living atlas analysis layers" and grp["owner"] == "esri_livingatlas":
                livingAtlasContentGroup = grp
        #
        # Unshare the groups, which will disable them. We could use the livingAtlas.disable_public_access() method,
        # but that works on all the groups returned by the internal group query which may include other groups that
        # should not be affected.
        #
        results = []
        url = livingAtlas._url + "/unshare"
        for grp in [livingAtlasGroup, livingAtlasContentGroup]:
            if grp != None:
                localLogger.write("Unsharing group: {}".format(grp.title))
                params = {
                    "f" : "json",
                    "groupId" : grp.id,
                    "type" : "Public"
                }
                result = livingAtlas._con.post(path = url, postdata = params)
                if result["status"] != "success":
                    localLogger.write("WARNING: Failed to unshare \"{}\": {}".format(grp.title, result))
                results.append(result["status"] == "success")
        return all(results)

    except Exception as ex:
        localLogger.write(FormatExceptions("ERROR: Unexpected exception thrown", ex))
        return False
    finally:
        localLogger.decIndent()

def configureSecurity(gis):
    localLogger.write("Configuration security options")
    localLogger.incIndent()

    try:
        if portal_config.securityConfig == None or len(portal_config.securityConfig) == 0:
            localLogger.write("No security configuration to apply")
            return True

        updConfig = json.loads(json.dumps(gis.admin.security.config))
        #
        # Remove items we are not expecting
        #
        for k in ["userStoreConfig", "groupStoreConfig"]:
            if k in updConfig:
                del updConfig[k]

        print("Current role: " + updConfig["defaultRoleForUser"])
        #
        # Add in our changes
        #
        for k in portal_config.securityConfig:
            updConfig[k] = portal_config.securityConfig[k]
        #
        # If the defaultRoleForUser property is not account_user or account_publisher, search the
        # roles to find the named role and substitute it for the role id
        #
        if "defaultRoleForUser" in portal_config.securityConfig and \
            portal_config.securityConfig["defaultRoleForUser"] not in ["account_user", "account_publisher"]:

            roleName = portal_config.securityConfig["defaultRoleForUser"]
            with localLogger.DisableAPILogging():
                existingRole = _findRole(gis, roleName)
            if existingRole == None:
                localLogger.write("ERROR: Role defined for defaultRoleForUser property does not exist: " + roleName)
                return False
            updConfig["defaultRoleForUser"] = existingRole.role_id
        #
        # Update the configuration
        #
        gis.admin.security.config = updConfig
        return True
    except Exception as ex:
        localLogger.write(FormatExceptions("ERROR: Unexpected exception thrown", ex))
        return False
    finally:
        localLogger.decIndent()

def configureGeneralProperties(gis):
    localLogger.write("Configuring general properties")
    localLogger.incIndent()

    try:
        if portal_config.generalProperties == None or len(portal_config.generalProperties) == 0:
            localLogger.write("No general properties to apply")
            return True

        updProperties = portal_config.generalProperties
        result = gis.update_properties(updProperties)
        return result
    except Exception as ex:
        localLogger.write(FormatExceptions("ERROR: Unexpected exception thrown", ex))
        return False
    finally:
        localLogger.decIndent()

def configureSystemProperties(gis):
    localLogger.write("Configuring system properties")
    localLogger.incIndent()

    try:
        if portal_config.systemProperties == None or len(portal_config.systemProperties) == 0:
            localLogger.write("No system properties to apply")
            return True

        system = gis.admin.system
        curProperties = system.properties
        updProperties = json.loads(json.dumps(curProperties))
        for k in portal_config.systemProperties:
            if k == "disableSignup":
               if portal_config.systemProperties[k] == True:
                   portal_config.systemProperties[k] = "true"
               elif portal_config.systemProperties[k] == False:
                   portal_config.systemProperties[k] = "false"
            updProperties[k] = portal_config.systemProperties[k]
        #
        # Check that we are actually going to update something, as calling update
        # will cause Portal to be restarted.
        #
        haveChanges = False
        for k in curProperties:
            if updProperties[k] != curProperties[k]:
                haveChanges = True
        for k in updProperties:
            if k not in curProperties:
                haveChanges = True

        if not haveChanges:
            localLogger.write("No system properties require changing")
            return True
        else:
            #
            # Using the following sends a gis.admin.system._con.get() call, which does not seem to work.
            # gis.admin.system.properties = updProperties
            # The following, therefore, uses a post command
            url = system._url + "/properties/update"
            params = {
                "f" : "json",
                "properties" : updProperties
            }
            localLogger.write("  Updating system properties - this may take several minutes")
            result = system._con.post(path=url, postdata=params)
            if "status" in result:
                return result["status"] == "success"
            else:
                return result
    except Exception as ex:
        localLogger.write(FormatExceptions("ERROR: Unexpected exception thrown", ex))
        return False
    finally:
        localLogger.decIndent()

def importConfigFile(filePath):
    """
    Loads the specified python file and exposes it as a module called portal_config
    """
    if not os.path.isfile(filePath):
        print("ERROR: File not found: " + filePath)
        return False

    moduleName = os.path.splitext(os.path.basename(filePath))[0]

    spec = importlib.util.spec_from_file_location(moduleName, filePath)
    if spec == None:
        print("ERROR: Could not load file " + filePath)
        return False
    else:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        globals()["portal_config"] = module
        return True

def main(args):

    results = []
    continueProcessing = True


    #read cmd line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-config','--config', help='PortalConfigSettings.py config file')
    parser.add_argument('-url','--url', help='Portal url of the form: https://portalname.domain.com/webadaptor')
    parser.add_argument('-u','--user', help='Administrator username')
    parser.add_argument('-p','--password', help='Administrator password')
    parser.add_argument('-l', '--log', help='Path to log file', default='python_process.log')

    args = parser.parse_args()


    #
    # Import the config file
    #
    if not importConfigFile(args.config):
        return 3
	
		
    try:
        localLogger.initialise(portal_config.logfile)
#        localLogger.initialise(None)

        gis = GIS(args.url, args.user, args.password, verify_cert=False)
        #
        # Install the portal certificate
        #
        results.append(installSSLCertificate(gis))
        if not all(results) and not portal_config.continueOnError:
            continueProcessing = False
        #
        # Configure roles
        #
        if continueProcessing:
            results.append(configureRoles(gis))
            if not all(results) and not portal_config.continueOnError:
                continueProcessing = False
        #
        # Disable the living atlas if required. Note that we do not re-enable it if
        # disableLivingAtlas has been set to True.
        #
        if continueProcessing and portal_config.disableLivingAtlas:
            results.append(disableLivingAtlas(gis))
            if not all(results) and not portal_config.continueOnError:
                continueProcessing = False
        #
        # Update security configuration
        #
        if continueProcessing:
            results.append(configureSecurity(gis))
            if not all(results) and not portal_config.continueOnError:
                continueProcessing = False
        #
        # Update general properties
        #
        if continueProcessing:
            results.append(configureGeneralProperties(gis))
            if not all(results) and not portal_config.continueOnError:
                continueProcessing = False
        #
        # Update system properties
        #
        if continueProcessing:
            results.append(configureSystemProperties(gis))
            if not all(results) and not portal_config.continueOnError:
                continueProcessing = False

    except Exception as ex:
        msg = FormatExceptions("Unexpected error", ex)
        if localLogger._rootLogger != None:
            localLogger.write(msg)
        else:
            print(msg)

    if all(results):
        localLogger.write("Script completed successfully")
        return 0
    elif continueProcessing:
        localLogger.write("Script completed with errors")
        return 1
    else:
        localLogger.write("Script execution failed")
        return 2

if __name__ == '__main__':
    exit_code = main(sys.argv)
    exit (exit_code)

