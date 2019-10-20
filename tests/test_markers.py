import py
import pytest


try:
    import mpi4py
except ImportError:
    mpi4py = None


MPI_ARGS = ("mpirun", "-n")
MPI_TEST_CODE = """
    import pytest

    @pytest.mark.mpi
    def test_size():
        from mpi4py import MPI
        comm = MPI.COMM_WORLD

        assert comm.size > 0

    @pytest.mark.mpi(min_size=2)
    def test_size_min_2():
        from mpi4py import MPI
        comm = MPI.COMM_WORLD

        assert comm.size >= 2

    @pytest.mark.mpi(min_size=4)
    def test_size_min_4():
        from mpi4py import MPI
        comm = MPI.COMM_WORLD

        assert comm.size >= 4

    @pytest.mark.mpi(2)
    def test_size_fail_pos():
        from mpi4py import MPI
        comm = MPI.COMM_WORLD

        assert comm.size > 0

    def test_no_mpi():
        assert True
"""
MPI_SKIP_TEST_CODE = """
    import pytest

    @pytest.mark.mpi_skip
    def test_skip():
        assert True
"""
MPI_XFAIL_TEST_CODE = """
    import pytest

    @pytest.mark.mpi_xfail
    def test_xfail():
        try:
            from mpi4py import MPI
            comm = MPI.COMM_WORLD
            assert comm.size < 2
        except ImportError:
            assert True
"""

def run_under_mpi(testdir_obj, *args, timeout=None, mpi_procs=2):
    """
    Based on testdir.runpytest_subprocess
    """
    p = py.path.local.make_numbered_dir(
        prefix="runpytest-", keep=None, rootdir=testdir_obj.tmpdir
    )
    args = ("--basetemp=%s" % p,) + args
    plugins = [x for x in testdir_obj.plugins if isinstance(x, str)]
    if plugins:
        args = ("-p", plugins[0]) + args
    args = MPI_ARGS + (str(mpi_procs),) + testdir_obj._getpytestargs() + args
    return testdir_obj.run(*args, timeout=timeout)


def test_mpi(testdir):
    testdir.makepyfile(MPI_TEST_CODE)

    result = testdir.runpytest()

    result.assert_outcomes(skipped=4, passed=1)


def test_mpi_with_mpi(testdir):
    testdir.makepyfile(MPI_TEST_CODE)

    result = run_under_mpi(testdir, "--with-mpi")

    if mpi4py is None:
        result.assert_outcomes(passed=1, error=4)
    else:
        result.assert_outcomes(passed=3, error=1, skipped=1)


def test_mpi_only_mpi(testdir):
    testdir.makepyfile(MPI_TEST_CODE)

    result = run_under_mpi(testdir, "--only-mpi")

    if mpi4py is None:
        result.assert_outcomes(error=4, skipped=1)
    else:
        result.assert_outcomes(passed=2, error=1, skipped=2)


def test_mpi_skip(testdir):
    testdir.makepyfile(MPI_SKIP_TEST_CODE)

    result = testdir.runpytest()

    result.assert_outcomes(passed=1)


def test_mpi_skip_under_mpi(testdir):
    testdir.makepyfile(MPI_SKIP_TEST_CODE)

    result = run_under_mpi(testdir, "--with-mpi")

    result.assert_outcomes(skipped=1)


def test_mpi_xfail(testdir):
    testdir.makepyfile(MPI_XFAIL_TEST_CODE)

    result = testdir.runpytest()

    result.assert_outcomes(passed=1)


def test_mpi_xfail_under_mpi(testdir):
    testdir.makepyfile(MPI_XFAIL_TEST_CODE)

    result = run_under_mpi(testdir, "--with-mpi")

    if mpi4py is None:
        result.assert_outcomes(xpassed=1)
    else:
        result.assert_outcomes(xfailed=1)
