Feature: Ask question
  Scenario: Submit valid math question
    Given a logged-in user
    When they submit a 100-character arithmetic question
    Then they see a loading indicator
    And an answer with 2-5 step bullets
    And a toast confirming save to history