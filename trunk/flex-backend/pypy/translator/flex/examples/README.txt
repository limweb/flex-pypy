This is a short list of things to do to create a new 
example:

- Create new directory and move/copy the new example to it

- Copy the py2flex.sh from "fun" example to the new dir

- Modify py2flex.sh (most probably you'll only need to change the name 
  of the .py file)

- svn add the new directory (it's recursive, will add the other two files)

- Execute py2flex.sh, which will create some support dirs

- Tell svn to ignore those support dirs, something like:

        $ svn propset svn:ignore "
        > ll_os_path
        > py
        > " .

  (note that the dir names are separated by a newline)

- Commit everything

- Smile and be happy, :)
