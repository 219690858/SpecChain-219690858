Feature: Manual validation tests (Headspace)
  These scenarios are derived from spec/spec_manual.md (FR1..FR12).

Feature: FR1 - Session stability (no crash/freeze)
  Scenario: Meditation plays 10 minutes (no crash/freeze)
    Given the user opens the app
    When the user opens any meditation session and presses play
    And the user listens for 10 minutes
    Then the session keeps playing and the app does not crash or freeze

  Scenario: Sleep session plays 10 minutes (no crash/freeze)
    Given the user opens the app
    When the user opens any sleep session and presses play
    And the user listens for 10 minutes
    Then the session keeps playing and the app does not crash or freeze

Feature: FR2 - Start session quickly
  Scenario: Open app and start session within 5 seconds
    Given the app is force closed
    When the user launches the app
    Then the user can start a session within 5 seconds

  Scenario: Cold start is not slow (within 5 seconds)
    Given the phone was restarted or the app was cleared from recents
    When the user launches the app
    Then the user can reach a playable session within 5 seconds

Feature: FR3 - Label locked content
  Scenario: Locked content is labeled in browse list
    Given the user is browsing courses or sessions
    When an item requires a subscription
    Then the item shows a clear "subscription required" label before selection

  Scenario: Locked content is labeled on details screen
    Given the user opens the details page of a paid item
    When the user views access information
    Then the screen clearly shows the item needs a subscription before play

Feature: FR4 - Show subscription price and renewal details
  Scenario: Before paying, price + renewal details are shown
    Given the user is in the subscription purchase flow
    When the user reaches the final confirmation screen
    Then price, billing period, and renewal date are shown on the same screen

  Scenario: Renewal details are visible (existing subscriber)
    Given the user has an active subscription
    When the user views subscription details
    Then price/billing period and next renewal date are clearly visible

Feature: FR5 - Cancellation instructions and Google Play link
  Scenario: Cancellation instructions exist in settings
    Given the user has an active subscription
    When the user opens account or subscription settings
    Then the settings show clear cancellation instructions

  Scenario: Settings has a link to Google Play subscription management
    Given the user has an active subscription
    When the user selects manage/cancel subscription
    Then Google Play subscription management opens for Headspace

Feature: FR6 - Downloads persist after restart
  Scenario: Download stays after restart
    Given the user downloads a session
    When the user force closes and reopens the app
    Then the downloaded session still appears in Downloads

  Scenario: Two downloads stay after restart
    Given the user downloads two sessions
    When the user closes and reopens the app
    Then both sessions still appear in Downloads

Feature: FR7 - Offline playback
  Scenario: Offline playback works (airplane mode)
    Given the user downloaded a session
    When the device is in airplane mode and the user plays the session
    Then the session plays and no offline error is shown

  Scenario: Offline playback works (no Wi-Fi/mobile data)
    Given the user downloaded a session
    When Wi-Fi and mobile data are disabled and the user plays the session
    Then the session plays without any network connectivity

Feature: FR8 - Login without loops
  Scenario: Login works with valid credentials (no loop)
    Given the user is on the login screen
    When the user enters valid credentials and submits login
    Then the user is signed in and not bounced back to login

  Scenario: Stay signed in after reopening
    Given the user is logged in
    When the user closes and reopens the app
    Then the user remains signed in

Feature: FR9 - Paid access for active subscribers
  Scenario: Paid content works for active subscriber
    Given the user has an active subscription
    When the user opens a paid session and presses play
    Then the session opens/plays and there is no subscription status error

  Scenario: No blocking "already have a subscription" error
    Given the user has an active subscription
    When the user navigates to paid content
    Then the app does not show a blocking subscription error and allows access

Feature: FR10 - Continue where left off
  Scenario: "Continue" shows up after starting a course
    Given the user started a course/session before
    When the user reopens the app
    Then a "Continue" option is shown in an obvious place

  Scenario: "Continue" resumes the next step
    Given the user completed one step in a course
    When the user taps "Continue"
    Then the app resumes the correct next step/session

Feature: FR11 - Support navigation items available
  Scenario: Care button reachable within 2 taps
    Given the user opens the main menu
    When the user looks for the Care button
    Then the Care button is visible and reachable within 2 taps

  Scenario: Support chat reachable within 2 taps
    Given the user opens the main menu
    When the user looks for support chat
    Then support chat is visible and reachable within 2 taps

Feature: FR12 - Haptics setting
  Scenario: Turn off haptics and confirm no vibration
    Given the user disables haptic feedback in settings
    When the user taps buttons in the app
    Then no haptic feedback happens

  Scenario: Turn haptics back on (control test)
    Given the user enables haptic feedback in settings
    When the user taps a button
    Then haptic feedback happens

