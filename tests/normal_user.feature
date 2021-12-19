Feature: Normal user permissions
    Make sure that normal users have very restricted permissions

    Scenario: Normal user in no group cannot see other persons
        Given a user who is not member of any group
        When the user searches for other persons
        Then the user should not see other persons

    Scenario: Normal user in a 'Kleingruppe' group can only see other group members
        Given a user who is only member of one 'Kleingruppe' group
        When the user searches for other persons
        Then the user should only see members of that group

    Scenario: Normal user in a 'Dienst' group can only see other group members
        Given a user who is only member of one 'Dienst' group
        When the user searches for other persons
        Then the user should only see members of that group

    Scenario: Normal user in a 'Gremium/Ausschuss' group can only see other group members
        Given a user who is only member of one 'Gremium/Ausschuss' group
        When the user searches for other persons
        Then the user should only see members of that group