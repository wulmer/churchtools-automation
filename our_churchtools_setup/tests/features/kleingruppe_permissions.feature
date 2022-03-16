Feature: User permissions in a 'Kleingruppe'
    Permissions for a 'Kleingruppe' are correct.

    Scenario: 'Leiter' user in a 'Kleingruppe' group can see level 3 details of other group members
        Given a user who is 'Leiter' of one 'Kleingruppe' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 3 details

    Scenario: 'Leiter' user in a 'Kleingruppe' group can see level 3 details of other group members
        Given a user who is 'Leiter' of one 'Kleingruppe' group
        When the user searches for other persons of that group
        Then the user should have the permission to edit other persons' details

    Scenario: 'Teamer' user in a 'Kleingruppe' group can see level 2 details of other group members
        Given a user who is 'Teamer' of one 'Kleingruppe' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 2 details

    Scenario: 'Teilnehmer' user in a 'Kleingruppe' group can see level 1 details of other group members
        Given a user who is 'Teilnehmer' of one 'Kleingruppe' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 1 details

    Scenario: 'Teilnahme beantragt' user in a 'Kleingruppe' group can not see other group members
        Given a user who is 'Teilnahme beantragt' of one 'Kleingruppe' group
        When the user searches for other persons of that group
        Then the user should not see other persons

    Scenario: 'zu löschen' user in a 'Kleingruppe' group can not see other group members
        Given a user who is 'zu löschen' of one 'Kleingruppe' group
        When the user searches for other persons of that group
        Then the user should not see other persons

    Scenario: 'Leiter' users in a 'Kleingruppe' group can create new persons in ChurchTools
        Given all users who are 'Leiter' of a 'Kleingruppe' group
        Then all those users should have the right to create new persons
    
    Scenario: 'Leiter' users in a 'Kleingruppe' group can invite persons to ChurchTools
        Given all users who are 'Leiter' of a 'Kleingruppe' group
        Then all those users should have the right to invite a person to ChurchTools