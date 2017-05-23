Feature: Unicode in source buffer
    In order to use Vdebug with all character sets
    As a user
    I want to debug code that uses Unicode characters

    Scenario: Debug a PHP file containing Unicode characters
        Given I have a file test.php containing
            """
            <?php
            $arr = array('中文' => '中文');
            ?>
            """
        And I start the debugger with the PHP script test.php
        When I step over
        Then the watch window should show $arr
