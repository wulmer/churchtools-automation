Feature: Members have proper status
    Make sure that all 'Mitarbeiter' have a proper status

    Scenario: Users who are 'Leiter' of a 'Dienst' group have 'Mitarbeiter' status
        Given all users who are 'Leiter' of a 'Dienst' group
        Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']

    Scenario: Users who are 'Mitarbeiter' of a 'Dienst' group have 'Mitarbeiter' status
        Given all users who are 'Leiter' of a 'Dienst' group
        Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']

    Scenario: Users who are 'Vorsitz' of a 'Gremium/Ausschuss' group have 'Mitarbeiter' status
        Given all users who are 'Vorsitz' of a 'Gremium/Ausschuss' group
        Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']

    Scenario: Users who are 'Stellv. Vorsitz' of a 'Gremium/Ausschuss' group have 'Mitarbeiter' status
        Given all users who are 'Stellv. Vorsitz' of a 'Gremium/Ausschuss' group
        Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']

    Scenario: Users who are 'Mitglieder' of a 'Gremium/Ausschuss' group have 'Mitarbeiter' status
        Given all users who are 'Mitglieder' of a 'Gremium/Ausschuss' group
        Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']

    Scenario: Users who are 'Leiter' of a 'Kleingruppe' group have 'Mitarbeiter' status
        Given all users who are 'Leiter' of a 'Kleingruppe' group
        Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']

    #Scenario: Users who are 'Teamer' of a 'Kleingruppe' group have 'Mitarbeiter' status
    #    Given all users who are 'Teamer' of a 'Kleingruppe' group
    #    Then these users have status in ['Mitarbeiter (HA)', 'Mitarbeiter (EA)', 'Systembenutzer']
