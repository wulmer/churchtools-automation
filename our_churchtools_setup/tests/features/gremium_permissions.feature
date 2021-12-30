Feature: User permissions in a 'Gremium'
    Permissions for a 'Gremium' are correct.

    Scenario: 'Mitglieder' user in a 'Gremium/Ausschuss' group can see level 2 details of other group members
        Given a user who is 'Mitglieder' of one 'Gremium/Ausschuss' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 2 details

    Scenario: 'Vorsitz' user in a 'Gremium/Ausschuss' group can see level 3 details of other group members
        Given a user who is 'Vorsitz' of one 'Gremium/Ausschuss' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 3 details

    Scenario: 'Stellv. Vorsitz' user in a 'Gremium/Ausschuss' group can see level 3 details of other group members
        Given a user who is 'Stellv. Vorsitz' of one 'Gremium/Ausschuss' group
        When the user searches for other persons of that group
        Then the user should see all members of that group
        And the user should only see up to level 3 details

    Scenario: 'Teilnahme beantragt' user in a 'Gremium/Ausschuss' group can not see other group members
        Given a user who is 'Teilnahme beantragt' of one 'Gremium/Ausschuss' group
        When the user searches for other persons of that group
        Then the user should not see other persons

    Scenario: 'zu löschen' user in a 'Gremium/Ausschuss' group can not see other group members
        Given a user who is 'zu löschen' of one 'Gremium/Ausschuss' group
        When the user searches for other persons of that group
        Then the user should not see other persons