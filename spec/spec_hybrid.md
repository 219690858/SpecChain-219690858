# Hybrid Specification (Headspace)

For Task 5 I went through the automated spec and updated it by hand. Main changes: traceability now uses hybrid groups H1-H5, persona names match the hybrid persona file, and I rewrote a few requirements that were vague or didn't match the right group.

## Requirement ID: FR_hybrid_1
- Description: [The app shall not crash or freeze during meditation sessions.]
- Source Persona: [Interrupted Session User]
- Traceability: [Derived from review group H1]
- Acceptance Criteria: [Given the app is in use on an Android device, When a meditation session is started, Then the app shall not crash or freeze for at least 30 minutes.]
- Notes: [Auto version was tied to one specific device model. I kept the 30-min no-crash rule but made it Android in general since the reviews aren't all Moto G86.]

## Requirement ID: FR_hybrid_2
- Description: [The app shall load meditation sessions within 5 seconds of initiating a session.]
- Source Persona: [Audio-Focused Listener]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given the app is launched on a compatible device, When a user selects a meditation session, Then the session shall start playing within 5 seconds.]
- Notes: [Still the 5-second rule from auto; updated persona and traceability to H2 since that group is about slow loading and performance.]

## Requirement ID: FR_hybrid_3
- Description: [The app shall provide offline access to downloaded meditation sessions.]
- Source Persona: [Audio-Focused Listener]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given a user has downloaded meditation sessions, When the device is offline, Then the user shall be able to access and play the downloaded sessions for at least 24 hours.]
- Notes: [Same idea as auto; H2 traceability makes sense since download/playback complaints are in that group.]

## Requirement ID: FR_hybrid_4
- Description: [The app shall not stop playback unexpectedly during meditation sessions.]
- Source Persona: [Audio-Focused Listener]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given a meditation session is playing, When the device is locked or the app is minimized, Then the session shall continue playing for at least 30 minutes without interruption.]
- Notes: [Lock/minimize while audio keeps going fits H2 better than other groups.]

## Requirement ID: FR_hybrid_5
- Description: [The app shall allow users to log in without encountering login loops.]
- Source Persona: [Locked-Out Returning User]
- Traceability: [Derived from review group H5]
- Acceptance Criteria: [Given a user attempts to log in through a linked account or email, When the credentials are correct, Then the user shall be logged in successfully within 10 seconds.]
- Notes: [Login loops show up a lot in H5; hybrid persona name matches that "can't get in" story.]

## Requirement ID: FR_hybrid_6
- Description: [The app shall display clear information about subscription access and paywall.]
- Source Persona: [Paying User Seeking Clarity]
- Traceability: [Derived from review group H3]
- Acceptance Criteria: [Given a user views the app's subscription options, When the user is not subscribed, Then the app shall display a clear message explaining the benefits and costs of subscription within 2 seconds.]
- Notes: [H3 is the subscription/money group; renamed the persona to something clearer so it's easier to trace back to the tests.]

## Requirement ID: FR_hybrid_7
- Description: [The app shall allow users to navigate away from a session and continue from the last playback position.]
- Source Persona: [Audio-Focused Listener]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given a user has started a meditation session, When the user navigates away and returns, Then playback shall resume from the last position within 10 seconds.]
- Notes: [Felt more like resume/playback than billing, so I moved traceability to H2 and spelled out "last playback position" in the acceptance criteria.]

## Requirement ID: FR_hybrid_8
- Description: [The app shall provide an option to turn off haptics.]
- Source Persona: [Interrupted Session User]
- Traceability: [Derived from review group H1]
- Acceptance Criteria: [Given the app's settings menu is accessed, When the user turns off haptics, Then haptics shall be disabled immediately.]
- Notes: [Requirement stayed the same; just updated persona and group labels to match hybrid.]

## Requirement ID: FR_hybrid_9
- Description: [The app shall display a clear error message when subscription access errors occur.]
- Source Persona: [Locked-Out Returning User]
- Traceability: [Derived from review group H5]
- Acceptance Criteria: [Given a subscription access error occurs, When the user views the error message, Then the message shall state the cause and at least one concrete next step within 5 seconds.]
- Notes: [The auto version said "potential resolution" which felt vague. Changed it to require at least one concrete next step so it's actually testable.]

## Requirement ID: FR_hybrid_10
- Description: [The app shall allow users to manage promotional notifications in-app.]
- Source Persona: [Catalog Browser]
- Traceability: [Derived from review group H4]
- Acceptance Criteria: [Given the user opens notification settings, When the user disables promotional notifications, Then the app shall not deliver promotional push notifications for 7 days unless the user turns them back on.]
- Notes: [FR_auto_10 was about counting marketing emails per week which I couldn't really ground in the reviews and isn't in-app anyway. Switched to an in-app notification toggle instead.]

## Requirement ID: FR_hybrid_11
- Description: [The app shall handle login through linked accounts without errors.]
- Source Persona: [Locked-Out Returning User]
- Traceability: [Derived from review group H5]
- Acceptance Criteria: [Given a user attempts to log in through a linked account, When the credentials are correct, Then the user shall be logged in successfully within 5 seconds.]
- Notes: [Same behavior as FR_auto_11; just updated persona name and H5 traceability to match Task 5.]
