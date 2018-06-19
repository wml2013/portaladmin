# Script to clean up the users, their content, groups and roles
from arcgis.gis import *
import argparse

try:
    #region read cmd line args
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='Portal url of the form: https://portalname.domain.com/webadaptor')
    parser.add_argument('-u','--user', help='Administrator username', default='siteadmin')
    parser.add_argument('-p','--password', help='Administrator password', default='x]984<ngb3!')
    parser.add_argument('-l', '--log', help='Path to log file', default='cleanup.log')

    args = parser.parse_args()
    #endregion

    # Read the log file in append mode
    log_file = open(args.log, 'a')

    log_file.write("\n")
    log_file.write("=====================================================================\n")
    log_file.write("RUNNING CLEANUP\n")

    gis = GIS(args.url, args.user, args.password)

    # region remove groups
    group_list = gis.groups.search("owner:" + args.user)
    log_file.write("Deleting groups\n")
    log_file.write("---------------\n")

    for group in group_list:
        try:
            log_file.write("\nDeleting " + group.title + "  ##  ")
            group.delete()
            log_file.write("success")
        except Exception as group_del_ex:
            log_file.write("Error deleting : " + str(group_del_ex))
    # endregion

    #region remove content for each user
    log_file.write("\n\nDeleting user content\n")
    log_file.write("---------------------\n")
    user_list = gis.users.search("")
    try:
        for user in user_list:
            log_file.write('\nUser : ' + user.username + " # ")
            if user.fullName in ['Administrator', 'Esri', 'Esri Navigation', 'siteadmin', 'admin']:
                log_file.write('skipped')
                continue

            user_content = gis.content.search('owner:{0}'.format(user.username))
            for item in user_content:
                log_file.write('\nDeleting : '+ item.title + " # ")
                delete_status = item.delete()
                log_file.write(str(delete_status)+ " | ")
            log_file.write('empty')

    except Exception as content_del_ex:
        log_file.write(str('content_del_ex'))
    #endregion

    # region remove users
    user_list = gis.users.search()
    log_file.write("\n\nDeleting users\n")
    log_file.write("--------------\n")

    for user in user_list:
        if user.username == "admin" or user.username.startswith("esri_") or user.username == "siteadmin" or user.username.startswith("kirk"):
            continue
        else:
            log_file.write("\nDeleting " + user.username + "  ##  ")
            user.delete()
            log_file.write("success")
    # endregion
    log_file.write("\n All clean")

    # region remove roles
    role_list = gis.users.roles.all(max_roles=100)
    role_list
    log_file.write("\n\nDeleting roles\n")
    log_file.write("--------------\n")

    for role in role_list:
        if role.name =='Administrator' or role.name == 'User' or role.name == 'Publisher' or role.name == 'Viewer':
            continue
        else:
              log_file.write("\nDeleting " + role.name + "  ##  ")
              role.delete()
              log_file.write("success")
    # endregion

    log_file.write("\n All clean")

    print("0 - Success, everything deleted that can be deleted.")
except:
    print("1 - Failed in deeleting.")