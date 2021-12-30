Feature: Every group has a leader/organizer
    Checks that every group has a leader or organizer.

    #Scenario: A 'Dienst' group has at least one leader.
    #    Given all active 'Dienst' groups
    #    Then there is at least one 'Leiter' in that group

    Scenario: A 'Gremium/Ausschuss' group has at least one leader.
        Given all active 'Gremium/Ausschuss' groups
        Then there is at least one 'Vorsitz' in that group
        
    Scenario: A 'Kleingruppe' group has at least one leader.
        Given all active 'Kleingruppe' groups
        Then there is at least one 'Leiter' or 'Teamer' in that group
        
    Scenario: A 'Veranstaltung' group has at least one leader.
        Given all active 'Veranstaltung' groups
        Then there is at least one 'Organisator' in that group
