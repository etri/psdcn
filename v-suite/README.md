# Validation suite (v-suite)


## Prerequisites

(Run 'remove-test-cases' if there are remnants of previous tests.)<br>
Run 'make-test-cases' to prepare command scripts for each test case.


## General Guidelines

Testcases are named as <strong>nn.scenario.role.seq</strong>.

#### nn (scenario number)
You can run the tests in an ascending order of scenario number.<br>
It is possible to skip some of them, but you are always expected to run them in ascending order of scenario numbers.
#### scenario (protocol or feature to be tested)
Some scenarios directly reflect PSDCNv3 commands such as pubadv, subtopic, etc. while some others are for feature names such as mobility, pending(-interest), etc.
#### role (who runs this script - publisher/subscriber)
Roles with a starting 'p' character (publisher, proceed) are to be run by publishers, while all others are to be run by subscribers.
#### seq (sequence number in a scenario)
Testcase names for a scenario are intentionally oredered to be run in sequence. However, there are cases when a role must do two or more separate tasks in sequence. <em>Seq</em> is the order number of the given role if there are more than one tasks for a given <em>nn.scenario.role</em>.

## Notes for a few testcases

Some testcases need special attention as below:

#### 07.pending
Subscribers have pending interests in this scenario and do not stop immediately until publisher publishes some data to the interest.<br>
You have to run 07.pending.subscriber.1 and 07.pending.subscriber.2 at two different systems(or terminal windows), and then run 07.proceed.publisher.2 at the publisher.

#### 11.mobility
You have to adjust the connection of the publisher for publisher.2 to a broker diffently from that for publisher.1 before running publisher.2.

#### 15.ratelimit
15.ratelimit.publisher populates 1000 datanames to the broker network. You don't have to run this more than once.<br><br>
15.ratelimit.subscriber was designed to be run many times, varying 'service_rate' of psdcnv3.config (100, 10, 1, 0.5,...).<br>
In order to guarantee fresh starts, do (stop-brokers; nfd-restart; modify 'service_rate', and start-broker broker-prefix) at each broker whenever a run for this script is needed.


## Cleanup

Run 'remove-test-cases' when validation tests are all done.


