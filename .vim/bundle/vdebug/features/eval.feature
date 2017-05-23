Feature: Evaluating expressions
    In order to evaluate variables in Vdebug
    As a user
    I want to see the evaluated variable in the watch window

    Scenario: Evaluating a PHP expression
        Given I have a file example.php containing
            """
            <?php
            $var1 = 1;
            ?>
            """
        And I start the debugger with the PHP script example.php
        When I evaluate $var1
        Then the watch window should show Eval of: '$var1'
