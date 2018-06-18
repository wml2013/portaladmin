# Portal URL or WebContext
portalURL = "https://www.startrek.com/argis"
#
#
# Logfile location and name
#
logfile = ".\\Logs\\portal_config.log"
#
# Whether to continue if an error occurs, or stop processing
#
continueOnError = False
#
# List of roles to be created.
# Currently use ESC roles.
#
roles = [
    {"name" : "ST User",
     "description" : "ST User",
     "privileges" : [
         'portal:user:joinGroup',
         'features:user:edit']
    },
    {"name" : "ST Viewer",
     "description" : "ST Viewer",
     "privileges" : [
         'portal:user:joinGroup']
    },
    {"name" : "ST Admin",
     "description" : "ST Admin",
     "privileges" : [
         'portal:admin:viewUsers',
         'portal:admin:updateUsers',
         'portal:admin:viewGroups',
         'portal:admin:deleteGroups',
         'portal:admin:updateGroups',
         'portal:admin:reassignGroups',
         'portal:admin:viewItems',
         'portal:admin:updateItems',
         'portal:admin:deleteItems',
         'portal:admin:reassignItems',
         'portal:publisher:publishTiles',
         'portal:user:createItem',
         'portal:user:shareToGroup',
         'portal:user:shareToOrg',
         'portal:user:shareGroupToOrg',
         'features:user:edit',
         'features:user:fulledit']
    },
        {"name" : "ST2 Admin",
     "description" : "ST2 Admin",
     "privileges" : [
         'portal:admin:viewUsers',
         'portal:admin:updateUsers',
         'portal:admin:viewGroups',
         'portal:admin:deleteGroups',
         'portal:admin:updateGroups',
         'portal:admin:reassignGroups',
         'portal:admin:viewItems',
         'portal:admin:updateItems',
         'portal:admin:deleteItems',
         'portal:admin:reassignItems',
         'portal:publisher:publishTiles',
         'portal:user:createItem',
         'portal:user:shareToGroup',
         'portal:user:shareToOrg',
         'portal:user:shareGroupToOrg',
         'features:user:edit',
         'features:user:fulledit']
    },
    {"name" : "ST Publisher3",
     "description" : "ST Publisher3",
     "privileges" : [
         'portal:admin:viewUsers',
         'portal:admin:updateUsers',
         'portal:admin:viewGroups',
         'portal:admin:deleteGroups',
         'portal:admin:updateGroups',
         'portal:admin:viewItems',
         'portal:admin:updateItems',
         'portal:admin:deleteItems',
         'portal:admin:reassignItems',
         'portal:publisher:publishTiles',
         'portal:user:createItem',
         'portal:user:shareToGroup',
         'portal:user:shareToOrg',
         'portal:user:shareGroupToOrg',
         'features:user:edit']
    }
]
#
# Whether Living Atlas is to be disabled
#
disableLivingAtlas = True
#
# General portal properties
# Update name and description as required
generalProperties = {
    "name" : "Star Trek Test portal",
    "description" : "Star Trek Test portal",
    "access" : "private",
    "allSSL" : True
}
#
# Security configuration
# For defaultRoleForUser, either specify one of the built in roles (account_user or account_publisher)
# or the name of a role created above.
#
securityConfig = {
    "defaultLevelForUser" : 1,
    "defaultRoleForUser" : "ST Viewer",
    "enableAutomaticAccountCreation" : False,
    "allowedProxyHosts" : None, # "www.startrek.com",
    "disableServicesDirectory" : False
}
#
# System properties
#
# If the WebContextURL is the same as the portalUrl defined at the top of this file, you
# can specify portalUrl as the value, otherwise specify the Url as a string.
#
systemProperties = {
    "WebContextURL" : portalURL,
    "disableSignup" : True
}
#
# SSL Certificate information
#
sslCertificates = {
    "alias" : "portal",
    "ssl_protocols" : [
        "TLSv1.2"#,
        #"TLSv1.1",
        #"TLSv1"
    ],
    "cipher_suites" : [
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384",
        #"TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384",
        #"TLS_DHE_RSA_WITH_AES_256_CBC_SHA256",
        #"TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_RSA_WITH_AES_256_GCM_SHA384" #,
        #"TLS_RSA_WITH_AES_256_CBC_SHA256",
        #"TLS_RSA_WITH_AES_256_CBC_SHA",
        #"TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
        #"TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
        #"TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
        #"TLS_DHE_RSA_WITH_AES_128_GCM_SHA256",
        #"TLS_DHE_RSA_WITH_AES_128_CBC_SHA256",
        #"TLS_DHE_RSA_WITH_AES_128_CBC_SHA",
        #"TLS_RSA_WITH_AES_128_GCM_SHA256",
        #"TLS_RSA_WITH_AES_128_CBC_SHA256",
        #"TLS_RSA_WITH_AES_128_CBC_SHA"
    ]
}
