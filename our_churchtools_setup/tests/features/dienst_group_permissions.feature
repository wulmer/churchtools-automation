Feature: User permissions in a 'Dienst' group
    Permissions for a 'Dienst' group are correct.

    Scenario: 'Mitarbeiter' user in a 'Dienst' group can see level 2 details of other group members
        Given a user who is 'Mitarbeiter' of one 'Dienst' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 2 details

    Scenario: 'Leiter' user in a 'Dienst' group can see level 3 details of other group members
        Given a user who is 'Leiter' of one 'Dienst' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 3 details

    Scenario: 'Teilnahme beantragt' user in a 'Dienst' group can not see other group members
        Given a user who is 'Teilnahme beantragt' of one 'Dienst' group
        When the user searches for other persons of that group
        Then the user should not see other persons

    Scenario: 'zu löschen' user in a 'Dienst' group can not see other group members
        Given a user who is 'zu löschen' of one 'Dienst' group
        When the user searches for other persons of that group
        Then the user should not see other persons
