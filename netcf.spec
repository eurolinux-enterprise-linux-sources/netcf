Name:           netcf
Version:        0.2.4
Release:        3%{?dist}%{?extra_release}
Summary:        Cross-platform network configuration library

Group:          System Environment/Libraries
License:        LGPLv2+
URL:            https://fedorahosted.org/netcf/
Source0:        https://fedorahosted.org/released/%{name}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# Default to skipping autoreconf.  Distros can change just this one
# line (or provide a command-line override) if they backport any
# patches that touch configure.ac or Makefile.am.
%{!?enable_autotools:%define enable_autotools 1}

# Patches
# One patch per line, in this format:
# Patch001: file1.patch
# Patch002: file2.patch
# ...
#
# The patches will automatically be put into the build source tree
# during the prep stage (using git, which is now required for an rpm
# build)
#

Patch001: netcf-Fix-name-of-DHCPV6C-variable-in-ifcfg-files.patch
Patch002: netcf-Fix-netmask-for-prefix-32.patch
Patch003: netcf-Report-file-path-and-reason-when-aug_save-fails.patch
Patch004: netcf-use-augeas-typedef-instead-of-struct-augeas.patch
Patch005: netcf-remove-unnecessary-calls-to-get_augeas.patch
Patch006: netcf-check-for-non-NULL-mac-after-calling-aug_get_mac.patch
Patch007: netcf-check-for-valid-pointer-on-all-returns-from-aug_get.patch
Patch008: netcf-local-copy-of-new-augeas-function-aug_escape_name.patch
Patch009: netcf-when-calling-aug_get-escape-special-characters-in-co.patch
Patch010: netcf-when-calling-aug_match-escape-special-characters-in-.patch
Patch011: netcf-when-calling-aug_fmt_match-escape-special-characters.patch
Patch012: netcf-when-calling-aug_rm-escape-special-characters-in-com.patch
Patch013: netcf-escape-interface-name-in-path-generated-by-xsl-trans.patch
Patch014: netcf-eliminate-netcf-specific-sysconfig.aug-lens.patch
Patch015: netcf-Remove-extraneous-single-quotes-from-IPV6ADDR_SECOND.patch

# git is used to build a source tree with patches applied (see the
# prep section)
BuildRequires: git

# Fedora 20 / RHEL-7 are where netcf first uses systemd. Although earlier
# Fedora has systemd, netcf still used sysvinit there.
%if 0%{?fedora} >= 20 || 0%{?rhel} >= 7
    %define with_systemd 1
%else
    %define with_systemd 0
%endif

%if %{with_systemd}
BuildRequires: systemd-units
Requires(post): systemd-units
Requires(post): systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units
%endif
%if 0%{?enable_autotools}
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: gettext-devel
BuildRequires: libtool
BuildRequires: /usr/bin/pod2man
%endif

BuildRequires:  readline-devel augeas-devel >= 0.5.2
BuildRequires:  libxml2-devel libxslt-devel

# force the --with-libnl1 option on F17/RHEL6 and earlier
%if (0%{?fedora} && 0%{?fedora} < 18) || (0%{?rhel} && 0%{?rhel} < 7)
%define with_libnl1 1
%else
%define with_libnl1 0
%endif

# require libnl3 on F18/RHEL7 and later
%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
BuildRequires:  libnl3-devel
%else
BuildRequires:  libnl-devel
%endif

Requires:       %{name}-libs = %{version}-%{release}

Provides: bundled(gnulib)

%description
Netcf is a library used to modify the network configuration of a
system. Network configurations are expressed in a platform-independent
XML format, which netcf translates into changes to the system's
'native' network configuration files.

%package        devel
Summary:        Development files for %{name}
Group:          Development/Libraries
Requires:       %{name}-libs = %{version}-%{release}
Requires:       pkgconfig

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package        libs
Summary:        Libraries for %{name}
Group:          System Environment/Libraries

# bridge-utils is needed because /sbin/ifup calls brctl
# if you create a bridge device
Requires:       bridge-utils

%description    libs
The libraries for %{name}.

%prep
%setup -q

# Patches have to be stored in a temporary file because RPM has
# a limit on the length of the result of any macro expansion;
# if the string is longer, it's silently cropped
%{lua:
    tmp = os.tmpname();
    f = io.open(tmp, "w+");
    count = 0;
    for i, p in ipairs(patches) do
        f:write(p.."\n");
        count = count + 1;
    end;
    f:close();
    print("PATCHCOUNT="..count.."\n")
    print("PATCHLIST="..tmp.."\n")
}

git init -q
git config user.name rpm-build
git config user.email rpm-build
git config gc.auto 0
git add .
git commit -q -a --author 'rpm-build <rpm-build>' \
           -m '%{name}-%{version} base'

COUNT=$(grep '\.patch$' $PATCHLIST | wc -l)
if [ $COUNT -ne $PATCHCOUNT ]; then
    echo "Found $COUNT patches in $PATCHLIST, expected $PATCHCOUNT"
    exit 1
fi
if [ $COUNT -gt 0 ]; then
    xargs git am <$PATCHLIST || exit 1
fi
echo "Applied $COUNT patches"
rm -f $PATCHLIST


%build
%if %{with_libnl1}
%define _with_libnl1 --with-libnl1
%endif
%if %{with_systemd}
    %define sysinit --with-sysinit=systemd
%else
    %define sysinit --with-sysinit=initscripts
%endif


%if 0%{?enable_autotools}
 autoreconf -if
%endif

%configure --disable-static \
           %{?_with_libnl1} \
           %{sysinit}
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT SYSTEMD_UNIT_DIR=%{_unitdir} \
     INSTALL="%{__install} -p"
find $RPM_BUILD_ROOT -name '*.la' -exec rm -f {} ';'

%clean
rm -rf $RPM_BUILD_ROOT

%preun libs

%if %{with_systemd}
    %systemd_preun netcf-transaction.service
%else
if [ $1 = 0 ]; then
    /sbin/chkconfig --del netcf-transaction
fi
%endif

%post libs

/sbin/ldconfig
%if %{with_systemd}
    %systemd_post netcf-transaction.service
    /bin/systemctl --no-reload enable netcf-transaction.service >/dev/null 2>&1 || :
%else
/sbin/chkconfig --add netcf-transaction
%endif

%postun libs

/sbin/ldconfig
%if %{with_systemd}
    %systemd_postun netcf-transaction.service
%endif

%files
%defattr(-,root,root,-)
%{_bindir}/ncftool
%{_mandir}/man1/ncftool.1*

%files libs
%defattr(-,root,root,-)
%{_datadir}/netcf
%{_libdir}/*.so.*
%if %{with_systemd}
%{_unitdir}/netcf-transaction.service
%else
%{_sysconfdir}/rc.d/init.d/netcf-transaction
%endif
%attr(0755, root, root) %{_libexecdir}/netcf-transaction.sh
%doc AUTHORS COPYING NEWS

%files devel
%defattr(-,root,root,-)
%doc
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/netcf.pc

%changelog
* Tue Apr 14 2015 Laine Stump <laine@redhat.com> - 0.2.4-3
 - resolves rhbz#1208894
 - Remove extraneous single quotes from IPV6ADDR_SECONDARIES
 - resolves rhbz#1208897
 - Bad parsing of network-scripts/ifcfg-xxxx files
 - resolves rhbz#1165966
 - resolves CVE-2014-8119
 - augeas path expression injection via interface name

* Mon Feb 09 2015 Laine Stump <laine@redhat.com> - 0.2.4-2
 - resolves rhbz#1113978
 - Fix name of DHCPV6C variable in ifcfg files
 - resolves rhbz#1116314
 - Fix netmask for prefix == 32
 - apply patches to source with git rather than patch

* Wed May 14 2014 Laine Stump <laine@redhat.com> - 0.2.4-1
 - rebase to netcf-0.2.4
 - resolves rhbz#851748
 - avoid use of uninitialized data when getting mac address
   resolves rhbz#1052156
 - eliminate duplicate quotes in bonding options
 - resolves rhbz#879055
 - wait for IFF_UP and IFF_RUNNING after calling ifup
 - don't require IFF_RUNNING for bridge devices
 - avoid memory leak in debian when listing interfaces
 - limit interface names to IFNAMSIZ-1 characters in length
 - support systemd for netcf-transaction

* Tue Aug 06 2013 Laine Stump <laine@redhat.com> - 0.1.9-4
  - resolves rhbz#844578
  - check IFF_RUNNING before considering and interface "active"
  - resolves rhbz#848722
  - fix ipcalc_netmask
* Fri Dec 21 2012 Laine Stump <laine@redhat.com> - 0.1.9-3
  - resolves rhbz#886862
  - libnl addr and link caches are not thread-safe, leading to
    libvirtd crashes

* Mon Sep 26 2011 Laine Stump <laine@redhat.com> - 0.1.9-2
  - resolves rhbz#728184
  - eliminate potential use of uninitialized index/pointer in add_bridge_info
  - resolves rhbz#736920
  - resolves rhbz#739505
  - fix missing vlan/bond/ethernet info in dumpxml --live

* Tue Jul 26 2011 Laine Stump <laine@redhat.com> - 0.1.9-1
  - rebase to netcf-0.1.9
  - resolves rhbz#616060
  - always add <bridge> element to bridge, even if there is no physdev present
  - resolves rhbz#713180
  - don't log error if interface isn't found in kernel during status report
  - resolves rhbz#713286
  - update gnulib

* Mon Jun 12 2011 Laine Stump <laine@redhat.com> - 0.1.8-1
  - rebase to netcf-0.1.8
  - resolves rhbz#616060
  - show ifup output in relevant error message
  - resolves rhbz#662057
  - pkgconfig file should not list augeas, libxml or libxslt
  - resolves rhbz#681078
  - Need to input 'quit' twice to quit ncftool after an erroneous command
  - resolves rhbz#703318
  - %desc field in specfile has a typo
  - resolves rhbz#705061
  - rebase netcf for RHEL6.2
  - resolves rhbz#708476
  - RFE: transaction-oriented API for handling host interfaces

* Thu Jan 13 2011 Laine Stump <laine@redhat.com> - 0.1.7-1
  - rebase to netcf-0.1.7
  - Resolves: rhbz#651032
  - remove all iptables manipulation
  - Resolves: rhbz#633346
  - Resolves: rhbz#629206

* Tue Jul 27 2010 Laine Stump <laine@redhat.com> - 0.1.6-4
- install missing sysconfig.aug file
- Resolves: rhbz#613886
- Don't delete the physical interface config when defining a vlan
- Resolves: rhbz#585112

* Mon Jul 19 2010 Laine Stump <laine@redhat.com> - 0.1.6-3
- properly handle quoted entries in sysconfig files
- Resolves: rhbz#613886

* Tue Jun 29 2010 Laine Stump <laine@redhat.com> - 0.1.6-2
- make miimon/arpmon in bond definitions optional
- Resolves: rhbz#585108
- properly deal with initializing a 0 length /etc/sysconfig/iptables file
- Resolves: rhbz#582905

* Thu Apr 22 2010 Laine Stump <laine@redhat.com> - 0.1.6-1
- New version

* Mon Nov 30 2009 David Lutterkort <lutter@redhat.com> - 0.1.5-1
- New version

* Thu Nov  5 2009 David Lutterkort <lutter@redhat.com> - 0.1.4-1
- New version

* Tue Oct 27 2009 David Lutterkort <lutter@redhat.com> - 0.1.3-1
- New version

* Fri Sep 25 2009 David Lutterkort <lutter@redhat.com> - 0.1.2-1
- New Version

* Wed Sep 16 2009 David Lutterkort <lutter@redhat.com> - 0.1.1-1
- Remove patch netcf-0.1.0-fix-initialization-of-libxslt.patch,
  included upstream

* Tue Sep 15 2009 Mark McLoughlin <markmc@redhat.com> - 0.1.0-3
- Fix libvirtd segfault caused by libxslt init issue (#523382)

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jul 13 2009 David Lutterkort <lutter@redhat.com> - 0.1.0-1
- BR on augeas-0.5.2
- Drop explicit requires for augeas-libs

* Wed Apr 15 2009 David Lutterkort <lutter@redhat.com> - 0.0.2-1
- Updates acording to Fedora review

* Fri Feb 27 2009 David Lutterkort <lutter@redhat.com> - 0.0.1-1
- Initial specfile
