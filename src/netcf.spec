Name:           netcf
Version:        0.1.9
Release:        1%{?dist}%{?extra_release}
Summary:        Cross-platform network configuration library

Group:          System Environment/Libraries
License:        LGPLv2+
URL:            https://fedorahosted.org/netcf/
Source0:        https://fedorahosted.org/released/%{name}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  readline-devel augeas-devel >= 0.5.2
BuildRequires:  libxml2-devel libxslt-devel
BuildRequires:  libnl-devel
Requires:       %{name}-libs = %{version}-%{release}

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

%description    libs
The libraries for %{name}.

%prep
%setup -q

%build
%configure --disable-static
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT INSTALL="%{__install} -p"
find $RPM_BUILD_ROOT -name '*.la' -exec rm -f {} ';'

%clean
rm -rf $RPM_BUILD_ROOT

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%{_bindir}/ncftool

%files libs
%defattr(-,root,root,-)
%{_datadir}/netcf
%{_libdir}/*.so.*
%{_sysconfdir}/rc.d/init.d/netcf-transaction
%doc AUTHORS COPYING NEWS

%files devel
%defattr(-,root,root,-)
%doc
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/netcf.pc

%changelog
* Tue Jul 26 2011 Laine Stump <laine@redhat.com> - 0.1.9-1
- always add <bridge> element to bridge, even if there is no physdev present
- don't log error if interface isn't found in kernel during status report
- allow building with C++
- update gnulib

* Fri Jun  3 2011 Laine Stump <laine@redhat.com> - 0.1.8-1
- new transactional change APIs: ncf_change_(begin|commit|rollback)
- add stdout/stderr to error text when an external program fails
- make error reporting of failed execs more exact/correct
- add "--system" to autogen.sh - sets all directories for standard system
  install.
- change sysconfdir and localstatedir during config if basedir is /usr.
- Remove unnecessary "Requires" of libxml2 and augeas from pkgconfig file
  to pulling in extra packages when building an application that uses netcf.
- Reorganize code to simplify porting to other platforms.

* Thu Sep 24 2010 Laine Stump <laine@redhat.com> - 0.1.7-1
- remove code that modifies iptables config for bridges
- register gnulib as a proper submodule
- don't delete physical interface config when defining a vlan
- properly handle quoted entries in sysconfig files.
- make miimon/arpmon optional

* Thu Apr 16 2010 Laine Stump <laine@redhat.com> - 0.1.6-1
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
- New Version

* Mon Jul 13 2009 David Lutterkort <lutter@redhat.com> - 0.1.0-1
- BR on augeas-0.5.2
- Drop explicit requires for augeas-libs

* Wed Apr 15 2009 David Lutterkort <lutter@redhat.com> - 0.0.2-1
- Updates acording to Fedora review

* Fri Feb 27 2009 David Lutterkort <lutter@redhat.com> - 0.0.1-1
- Initial specfile
