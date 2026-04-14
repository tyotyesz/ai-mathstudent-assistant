Feature: Empty state
  Scenario: See empty history when no conversations
    Given a new user with no history
    When they open the Home page
    Then they see an empty history message and CTA "Ask a question"