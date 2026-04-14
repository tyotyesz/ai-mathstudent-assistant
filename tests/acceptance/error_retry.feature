Feature: Error and retry
  Scenario: Backend error with retry
    Given the backend returns a 500 error
    When the user submits a question
    Then an error panel appears with guidance
    When they click Retry
    Then the request is retried and succeeds
    And the answer replaces the error panel