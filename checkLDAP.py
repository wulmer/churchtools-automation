import os
import subprocess

import requests
from deepdiff import DeepDiff


def check_churchtools_ldap_server():
    print("Checking ChurchTools LDAP Server...")
    subprocess.check_output(
        [
            "ldapsearch",
            "-H",
            "ldaps://ldap.church.tools:636",
            "-x",
            "-w",
            f'{os.environ["LDAP_PW"]}',
            "-D",
            f'cn=root,ou=users,o={os.environ["LDAP_SUBDOMAIN"]}',
            "-z",
            "1",
            "-b",
            f'ou=users,o={os.environ["LDAP_SUBDOMAIN"]}',
        ]
    )
    print("OK")


def check_nextcloud_settings():
    print("Checking NextCloud LDAP settings...")
    response = requests.get(
        url=f"{os.environ['NEXTCLOUD_BASE_URL']}/ocs/v2.php/apps/user_ldap/api/v1/config/s01",
        auth=(os.environ["NEXTCLOUD_ADMIN_USER"], os.environ["NEXTCLOUD_ADMIN_TOKEN"]),
        headers={
            "OCS-APIRequest": "true",
        },
        params={"format": "json"},
    )
    response.raise_for_status()
    LDAP_SUBDOMAIN = os.environ["LDAP_SUBDOMAIN"]
    ldap_config = response.json()["ocs"]["data"]
    expected_config = {
        "hasMemberOfFilterSupport": "1",
        "homeFolderNamingRule": "",
        "lastJpegPhotoLookup": "0",
        "ldapAdminGroup": "",
        "ldapAgentName": f"cn=root,ou=users,o={LDAP_SUBDOMAIN}",
        "ldapAgentPassword": "***",
        "ldapAttributeAddress": "",
        "ldapAttributeBiography": "",
        "ldapAttributeFediverse": "",
        "ldapAttributeHeadline": "",
        "ldapAttributeOrganisation": "",
        "ldapAttributePhone": "",
        "ldapAttributeRole": "",
        "ldapAttributeTwitter": "",
        "ldapAttributeWebsite": "",
        "ldapAttributesForGroupSearch": "",
        "ldapAttributesForUserSearch": "",
        "ldapBackgroundHost": "",
        "ldapBackgroundPort": "",
        "ldapBackupHost": "",
        "ldapBackupPort": "",
        "ldapBase": f"ou=users,o={LDAP_SUBDOMAIN}",
        "ldapBaseGroups": f"ou=groups,o={LDAP_SUBDOMAIN}",
        "ldapBaseUsers": f"ou=users,o={LDAP_SUBDOMAIN}",
        "ldapCacheTTL": "600",
        "ldapConfigurationActive": "1",
        "ldapConnectionTimeout": "15",
        "ldapDefaultPPolicyDN": "",
        "ldapDynamicGroupMemberURL": "",
        "ldapEmailAttribute": "mail",
        "ldapExperiencedAdmin": "0",
        "ldapExpertUUIDGroupAttr": "",
        "ldapExpertUUIDUserAttr": "uid",
        "ldapExpertUsernameAttr": "",
        "ldapExtStorageHomeAttribute": "",
        "ldapGidNumber": "gidNumber",
        "ldapGroupDisplayName": "cn",
        "ldapGroupFilter": "objectClass=group",
        "ldapGroupFilterGroups": "",
        "ldapGroupFilterMode": "1",
        "ldapGroupFilterObjectclass": "",
        "ldapGroupMemberAssocAttr": "uniqueMember",
        "ldapHost": "ldaps://ldap.church.tools",
        "ldapIgnoreNamingRules": "",
        "ldapLoginFilter": f"(&(&(|(objectclass=CTPerson))(|(memberof=cn=auto-gruppe: alle mitarbeiter,ou=groups,o={LDAP_SUBDOMAIN})))(|(uid=%uid)(|(mailPrimaryAddress=%uid)(mail=%uid))))",
        "ldapLoginFilterAttributes": "",
        "ldapLoginFilterEmail": "1",
        "ldapLoginFilterMode": "0",
        "ldapLoginFilterUsername": "1",
        "ldapMatchingRuleInChainState": "unknown",
        "ldapNestedGroups": "0",
        "ldapOverrideMainServer": "",
        "ldapPagingSize": "500",
        "ldapPort": "636",
        "ldapQuotaAttribute": "",
        "ldapQuotaDefault": "",
        "ldapTLS": "0",
        "ldapUserAvatarRule": "default",
        "ldapUserDisplayName": "displayname",
        "ldapUserDisplayName2": "",
        "ldapUserFilter": f"(&(|(objectclass=CTPerson))(|(memberof=cn=auto-gruppe: alle mitarbeiter,ou=groups,o={LDAP_SUBDOMAIN})))",
        "ldapUserFilterGroups": "Auto-Gruppe: Alle Mitarbeiter",
        "ldapUserFilterMode": "1",
        "ldapUserFilterObjectclass": "CTPerson",
        "ldapUuidGroupAttribute": "auto",
        "ldapUuidUserAttribute": "auto",
        "markRemnantsAsDisabled": "0",
        "turnOffCertCheck": "0",
        "turnOnPasswordChange": "0",
        "useMemberOfToDetectMembership": "1",
    }

    is_different = DeepDiff(expected_config, ldap_config)
    assert not is_different, is_different
    print("OK")


def main():
    check_churchtools_ldap_server()
    check_nextcloud_settings()


if __name__ == "__main__":
    main()
