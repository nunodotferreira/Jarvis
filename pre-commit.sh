nosetests
code=$?

if [ "$code" == "0" ]; then
exit -1
fi

echo -n "Not all tests pass. Commit (y/n): "
read response
if [ "$response" == "y" ]; then
exit 0
fi

exit $code
