# *-* coding: utf-8 *-*
from .conftest import use


@use('trace_in_script.py')
def test_with_trace(socket):
    socket.start()

    msg = socket.receive()
    assert msg.command == 'Init'
    assert 'cwd' in msg.data

    msg = socket.receive()
    assert msg.command == 'Title'
    assert msg.data.title == 'Wdb'
    assert msg.data.subtitle == 'Stepping'

    msg = socket.receive()
    assert msg.command == 'Trace'
    current_trace = msg.data.trace[-1]
    assert current_trace.code == 'a = 2'
    assert current_trace.current is True
    assert 'scripts/trace_in_script.py' in current_trace.file
    assert current_trace.flno == 11
    assert current_trace.function == 'fun2'
    assert current_trace.llno == 15
    assert current_trace.lno == 13

    msg = socket.receive()
    assert msg.command == 'SelectCheck'
    assert msg.data.frame.function == 'fun2'
    file = msg.data.name

    msg = socket.receive()
    assert msg.command == 'Watched'
    assert msg.data == {}

    socket.send('File', file)
    msg = socket.receive()
    assert msg.command == 'Select'
    assert msg.data.name == file
    assert len(msg.data.file) == 261

    socket.send('Continue')

    # Tracing
    msg = None
    while not msg:
        try:
            msg = socket.receive()
        except Exception as e:
            msg = None
            assert type(e) == EOFError

    assert msg.command == 'Title'
    assert msg.data.title == 'Wdb'
    assert msg.data.subtitle == 'Stepping'

    msg = socket.receive()
    assert msg.command == 'Trace'
    current_trace = msg.data.trace[-1]
    assert current_trace.code == "print('The end')"
    assert current_trace.current is True
    assert 'scripts/trace_in_script.py' in current_trace.file
    assert current_trace.flno == 3
    assert current_trace.function == '<module>'
    assert current_trace.llno == 24
    assert current_trace.lno == 24

    msg = socket.receive()
    assert msg.command == 'SelectCheck'
    assert msg.data.frame.function == '<module>'
    file = msg.data.name

    msg = socket.receive()
    assert msg.command == 'Watched'
    assert msg.data == {}

    socket.send('File', file)
    msg = socket.receive()
    assert msg.command == 'Select'
    assert msg.data.name == file
    assert len(msg.data.file) == 261

    socket.send('Continue')
    socket.join()


@use('error_in_with.py')
def test_with_error_in_trace(socket):
    socket.start()
    # The first to stop must be the one with the full trace
    msg = socket.receive()
    assert msg.command == 'Init'
    assert 'cwd' in msg.data

    socket.assert_position(
        title='ZeroDivisionError',
        code='return i / 0',
        exception="ZeroDivisionError")
    socket.send('Return')
    socket.assert_position(code='return 2', return_="2")
    socket.send('Next')
    socket.assert_position(code='print(d + a)', line=24)

    socket.send('Continue')
    socket.join()


@use('error_in_with_advanced.py')
def test_with_error_in_trace_advanced(socket):
    socket.start()
    # The first to stop must be the one with the full trace on parent
    msg = socket.receive()
    assert msg.command == 'Init'
    assert 'cwd' in msg.data

    for i in range(2):
        socket.assert_position(
            title='ZeroDivisionError',
            code='return i / 0',
            exception="ZeroDivisionError")
        socket.send('Next')
        socket.assert_position(
            code='return i / 0',
            return_='None',
            subtitle='Returning from make_error with value None')
        # Full trace catch exception at everly traced level
        socket.send('Next')
        socket.assert_position(
            title='ZeroDivisionError',
            code='return i / 0',
            bottom_code='parent()' if not i else 'grandparent()',
            exception="ZeroDivisionError")

        socket.send('Next')
        socket.assert_position(code='except ZeroDivisionError:')
        socket.send('Continue')
    socket.join()


@use('error_in_with_below.py')
def test_with_error_in_trace_below(socket):
    socket.start()
    # The first to stop must be the one with the full trace on parent
    msg = socket.receive()
    assert msg.command == 'Init'
    assert 'cwd' in msg.data

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='uninteresting_function_not_catching(1)',
        bottom_line=54)
    socket.send('Continue')

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='uninteresting_function_catching(1)',
        bottom_line=61)

    socket.send('Continue')

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='one_more_step(uninteresting_function_not_catching, 2)',
        bottom_line=78)
    socket.send('Continue')

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='one_more_step(uninteresting_function_catching, 2)',
        bottom_line=84)
    socket.send('Continue')
    socket.join()


@use('error_in_with_under.py')
def test_with_error_in_trace_under(socket):
    socket.start()
    # The first to stop must be the one with the full trace on parent
    msg = socket.receive()
    assert msg.command == 'Init'
    assert 'cwd' in msg.data

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='uninteresting_function_not_catching(1)',
        bottom_line=54)
    socket.send('Continue')

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='uninteresting_function_catching(1)',
        bottom_line=61)

    socket.send('Continue')

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='one_more_step(uninteresting_function_not_catching, 2)',
        bottom_line=78)
    socket.send('Continue')

    socket.assert_position(
        title='ZeroDivisionError',
        code='return below / 0',
        exception="ZeroDivisionError",
        bottom_code='one_more_step(uninteresting_function_catching, 2)',
        bottom_line=84)
    socket.send('Continue')
    socket.join()
