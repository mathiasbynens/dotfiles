Feature: Valid file names
    In order to use Vdebug with all file names
    As a user
    I want to debug a file with any valid system characters

    Scenario: Debug a PHP file containing spaces
        Given I have a file My File.php containing
            """
            <?php
            $var = 1;
            ?>
            """
        And I start the debugger with the PHP script My File.php
        When I step over
        Then the watch window should show $var

    Scenario: Debug a PHP file with a space in the directory
        Given I have a file A Path/myfile.php containing
            """
            <?php
            $var = 1;
            ?>
            """
        And I start the debugger with the PHP script A Path/myfile.php
        When I step over
        Then the watch window should show $var
