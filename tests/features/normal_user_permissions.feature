Feature: Normal user permissions
    Make sure that normal users have very restricted permissions

    Scenario: Normal user in no group cannot see other persons
        Given a user who is not member of any group
        When the user searches for other persons
        Then there should be only public search results

    Scenario: Normal user in no group can see all groups
        Given a user who is not member of any group
        When the user searches for groups
        Then there should be only public search results
        #Then the user should see all non-hidden groups