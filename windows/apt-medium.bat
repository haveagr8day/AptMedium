
# needs some FreeDOS Hacker
# Option parsing is missing
# md5sum checking missing

$WGET_CMD=$APT_MEDIUM_DIR/w23bin/wget

	if $MACHINE_NAME = "" #(download for all machines)
	  $MACHINE_NAMES="'dir $APT_MEDIUM_DIR/machine'"
	else $MACHINE_NAMES="$MACHINE_NAME"

	for  $MACHINE_NAME in $MACHINE_NAMES do
	   $WGET_CMD --directory-prefix=$APT_MEDIUM_DIR/lists -c -x -i $APT_MEDIUM_DIR/machine/$MACHINE_lists_dl_uris
	   $WGET_CMD --directory-prefix=$APT_MEDIUM_DIR/archives -c -i $APT_MEDIUM_DIR/machine/$MACHINE_pkg_dl_uris

	   rm $APT_MEDIUM_DIR/machine/$MACHINE_lists_dl_uris
	   rm $APT_MEDIUM_DIR/machine/$MACHINE_pkg_dl_uris
	done