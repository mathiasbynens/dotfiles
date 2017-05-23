Feature: Correct window setup
    In order to use Vdebug with all window panels
    As a user
    I want to see correct watch, stack and status information

    Scenario: The status window
        Given I have a file example.php containing
            """
            <?php
            $var1 = 1;
            ?>
            """
        When I start the debugger with the PHP script example.php
        Then the status should be break
        And the status window should contain :9000

    Scenario: The watch window
        Given I have a file example.php containing
            """
            <?php
            $var1 = 1;
            $var2 = array("hello", "world");
            ?>
            """
        And I start the debugger with the PHP script example.php
        When I step over
        Then the watch window should show $var1
        And the watch window should show $var2
        And the watch window variable $var1 should be (int) 1
        And the watch window variable $var2 should be (uninitialized)

    Scenario: The stack window
        Given I have a file example.php containing
            """
            <?php
            $var1 = 1;
            $var2 = array("hello", "world");
            ?>
            """
        And I start the debugger with the PHP script example.php
        When I step over
        Then the first item on the stack should show the file example.php
        And the first item on the stack should show line 3

    Scenario: Reading the stack window with multiple files
        Given I have a file example.php containing
            """
            <?php
            include "example2.php";
            ?>
            """
        And I have a file example2.php containing
            """
            <?php
            $var1 = 1;
            $var2 = array("hello", "world");
            ?>
            """
        And I start the debugger with the PHP script example.php
        When I step in
        Then item 1 on the stack should show the file example2.php
        And item 1 on the stack should show line 2
        And item 2 on the stack should show the file example.php
        And item 2 on the stack should show line 2
