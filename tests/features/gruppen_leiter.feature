Feature: Every group has a leader/organizer
    Checks that every group has a leader or organizer.

    Scenario: A 'Dienst' group has at least one leader.
        Given all 'Dienst' groups
        Then there is at least one 'Leiter' in that group

    Scenario: A 'Gremium/Ausschuss' group has at least one leader.
        Given all 'Gremium/Ausschuss' groups
        Then there is at least one 'Vorsitz' in that group
        
    Scenario: A 'Kleingruppe' group has at least one leader.
        Given all 'Kleingruppe' groups
        Then there is at least one 'Leiter' in that group
        
    Scenario: A 'Veranstaltung' group has at least one leader.
        Given all 'Veranstaltung' groups
        Then there is at least one 'Organisator' in that group
