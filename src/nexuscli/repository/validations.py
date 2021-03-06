from nexuscli.nexus_util import validate_strings

try:
    from urllib.parse import urlparse  # Python 3
except ImportError:
    from urlparse import urlparse      # Python 2


# TODO: remove when all known formats/types are supported
KNOWN_TYPES = ['group', 'hosted', 'proxy']
KNOWN_FORMATS = [
    'bower', 'docker', 'gitlfs', 'maven', 'npm', 'nuget', 'pypi', 'raw',
    'rubygems', 'yum']
SUPPORTED_FORMATS = [
    'bower', 'maven', 'npm', 'nuget', 'pypi', 'raw', 'rubygems', 'yum']
SUPPORTED_TYPES = ['hosted', 'proxy']
LAYOUT_POLICIES = ['PERMISSIVE', 'STRICT']
VERSION_POLICIES = ['RELEASE', 'SNAPSHOT', 'MIXED']
WRITE_POLICIES = ['ALLOW', 'ALLOW_ONCE', 'DENY']


def is_target_supported(target, value, known, supported):
    """Validate whether the a target argument is known and supported"""
    if value not in known:
        raise ValueError(
            '{target}={value} must be one of {known}'.format(
                **locals()))

    if value not in supported:
        raise NotImplementedError(
            '{target}={value}; supported {target}s: {supported}'.format(
                **locals()))


def _upcase_values(raw_repo, targets=[]):
    for key in targets:
        value = raw_repo.get(key)
        if value is not None:
            raw_repo[key] = value.upper()


def args_to_raw_repo(args):
    raw = dict(args)
    _upcase_values(raw, ['layout_policy', 'write_policy', 'version_policy'])
    return raw


def check_create_args(repo_type, **kwargs):
    """
    Validate arguments for
    :py:meth:`nexuscli.nexus_repository.Repository.create()

    Raises:
        :py:class:`ValueError`
            If the value of a given argument is invalid or unsupported, or if
            unrecognised keyword arguments are given.
        :py:class:`TypeError`
            If the type of a given argument has the wrong object type.
        :py:class:`NotImplementedError`
            If the combination of arguments isn't yet supported.

    :param repo_type: as given to
        :py:meth:`nexuscli.nexus_repository.Repository.create()
    :param kwargs: as given to
        :py:meth:`nexuscli.nexus_repository.Repository.create()
    """
    if not validate_strings(repo_type):
        raise TypeError('repo_type ({}) must be of string type'.format(
            type(repo_type)))
    is_target_supported('repo_type', repo_type, KNOWN_TYPES, SUPPORTED_TYPES)

    try:
        remaining_args = check_common_args(**kwargs)
        remaining_args = check_type_args(repo_type, **remaining_args)
    except KeyError as e:
        raise KeyError('Missing required keyword argument: {}'.format(e))

    ignore_extra = remaining_args.pop('ignore_extra_kwargs', False)
    if remaining_args and not ignore_extra:
        raise ValueError('Unrecognised keyword arguments: {}'.format(
            remaining_args.keys()))


def check_common_args(**kwargs):
    name = kwargs.pop('name')
    format_ = kwargs.pop('format')
    if not validate_strings(name, format_):
        raise TypeError(
            'name ({0}) and format ({1}) must all be of string type'.format(
                *map(type, [name, format_])))
    is_target_supported('format', format_, KNOWN_FORMATS, SUPPORTED_FORMATS)

    blob_store_name = kwargs.pop('blob_store_name')
    # TODO: validate that blob_store_name exists on server
    assert blob_store_name

    strict_content_type_v = kwargs.pop('strict_content_type_validation')
    if not isinstance(strict_content_type_v, bool):
        raise TypeError(
            'strict_content_type_validation ({}) must be bool'.format(
                type(strict_content_type_v)))

    remaining_args = check_format_args(format_, **kwargs)
    return remaining_args


def check_format_args(repo_format, **kwargs):
    try:
        check_specific = globals()['check_format_args_' + repo_format]
    except KeyError:
        # nothing specific to check on this repository format
        return kwargs

    return check_specific(**kwargs)


def check_format_args_maven(**kwargs):
    version_policy = kwargs.pop('version_policy')
    layout_policy = kwargs.pop('layout_policy')
    is_target_supported(
        'version_policy', version_policy, VERSION_POLICIES, VERSION_POLICIES)
    is_target_supported(
        'layout_policy', layout_policy, LAYOUT_POLICIES, LAYOUT_POLICIES)

    return kwargs


def check_format_args_yum(**kwargs):
    depth = kwargs.pop('depth')
    if depth < 0 or depth > 5:
        raise ValueError('depth={}; must be between 0-5'.format(depth))

    return kwargs


def check_type_args(repo_type, **kwargs):
    check_specific = globals()['check_type_args_' + repo_type]
    return check_specific(**kwargs)


def check_type_args_hosted(**kwargs):
    write_policy = kwargs.pop('write_policy')
    is_target_supported(
        'write_policy', write_policy, WRITE_POLICIES, WRITE_POLICIES)

    return kwargs


def check_type_args_proxy(**kwargs):
    remote_url = kwargs.pop('remote_url')
    parsed_url = urlparse(remote_url)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise ValueError('remote_url={} is not a valid URL'.format(remote_url))

    return kwargs
