%define gettext_package dbus

%define expat_version           1.95.5
%define glib2_version           2.2.0
%define qt_version              3.1.0
%define pyrex_version		0.9.2.1
%define gtk2_version		2.4.0
%define libselinux_version	1.15.2	

%define dbus_user_uid           81

Summary: D-BUS message bus
Name: dbus
Version: 0.22
Release: 9 
URL: http://www.freedesktop.org/software/dbus/
Source0: %{name}-%{version}.tar.gz
Source1: messagebus
License: AFL/GPL
Group: System Environment/Libraries
BuildRoot: %{_tmppath}/%{name}-root
PreReq: chkconfig /usr/sbin/useradd
BuildPreReq: libtool
#BuildRequires: redhat-release 
BuildRequires: expat-devel >= %{expat_version}
BuildRequires: libxml2-devel
BuildRequires: glib2-devel >= %{glib2_version}
#BuildRequires: qt-devel    >= %{qt_version}
BuildRequires: Pyrex	   >= %{pyrex_version}
#BuildRequires: gtk2-devel  >= %{gtk_version}
BuildRequires: libselinux-devel >= %{libselinux_version}

Requires: libselinux >= %{libselinux_version}

Conflicts: cups < 1:1.1.20-4

Patch1: dbus-0.13-uid.patch
Patch2: dbus-0.21-console-auth.patch
Patch3: dbus-0.22-python-int64.patch 
Patch4: dbus-0.22-servicedir.patch

%description

D-BUS is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.

%package devel
Summary: Libraries and headers for D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}

%description devel

Headers and static libraries for D-BUS.

%package glib
Summary: GLib-based library for using D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}

%description glib

D-BUS add-on library to integrate the standard D-BUS library with
the GLib thread abstraction and main loop.

%if 0
%package gtk
Summary: GTK based tools
Group: Development/Tools 
Requires: %name = %{version}-%{release}
Requires: gtk2 >= %{gtk_version}
%description gtk

D-BUS tools written using the gtk+ GUI libaries

%endif

%if 0

%package qt
Summary: Qt-based library for using D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}

%description qt

D-BUS add-on library to integrate the standard D-BUS library with
the Qt thread abstraction and main loop.

%endif

%package x11
Summary: X11-requiring add-ons for D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}

%description x11

D-BUS contains some tools that require Xlib to be installed, those are
in this separate package so server systems need not install X.

%package python 
Summary: python bindings for D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}
                                                                                
%description python 
                                                                                
D-BUS python bindings for use with python programs.   

%prep
%setup -q

%patch1 -p1 -b .uid
%patch2 -p0 -b .console-auth
%patch3 -p0 -b .python-int64
%patch4 -p1 -b .servicedir

autoreconf -f -i

%build

COMMON_ARGS="--enable-glib=yes --enable-qt=no --enable-selinux=yes --disable-gtk --with-init-scripts=redhat"

if test -d %{_libdir}/qt-3.1 ; then
   export QTDIR=%{_libdir}/qt-3.1
else
   echo "WARNING: %{_libdir}/qt-3.1 does not exist"
fi

#### Fix user to run the system bus as
perl -pi -e 's@<user>[a-z]+</user>@<user>%{dbus_user_uid}</user>@g' bus/system.conf*

### this is some crack because bits of dbus can be 
### smp-compiled but others don't feel like working
function make_fast() {
        ### try to burn through it with SMP a couple times
        make %{?_smp_mflags} || true
        make %{?_smp_mflags} || true

        ### then do a real make and don't ignore failure
        make
}

%ifarch ia64
#FIXME: workaround for gcc-3.4 bug which causes python bindings build to hand on ia64 arches
CFLAGS="$RPM_OPT_FLAGS -O1"
export CFLAGS
%endif
#### Build once with tests to make check
%configure $COMMON_ARGS --enable-tests=yes --enable-verbose-mode=yes --enable-asserts=yes
make_fast
exit 0
DBUS_VERBOSE=1 make check > dbus-check.log 2>&1 || (cat dbus-check.log && false)

#### Clean up and build again 
make clean 

%configure $COMMON_ARGS --disable-tests --disable-verbose-mode --disable-asserts
make_fast

%install
rm -rf %{buildroot}

%makeinstall

rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

#hack to get around a bug in the python distutils on 64 bit archs
%if "%{_lib}" == "lib64"
cp -r $RPM_BUILD_ROOT/usr/lib/* $RPM_BUILD_ROOT%{_libdir}/
rm -rf $RPM_BUILD_ROOT/usr/lib
perl -pi -e 's/\/usr\/lib\//\/usr\/lib64\//g' INSTALLED_FILES
%endif

#install precompiled messagebus init script
install -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/messagebus

## %find_lang %{gettext_package}

%clean
rm -rf %{buildroot}

%pre
# Add the "dbus" user
/usr/sbin/useradd -c 'System message bus' -u %{dbus_user_uid} \
	-s /sbin/nologin -r -d '/' dbus 2> /dev/null || :

%post
/sbin/ldconfig
/sbin/chkconfig --add messagebus

%preun
if [ $1 = 0 ]; then
    service messagebus stop > /dev/null 2>&1
    /sbin/chkconfig --del messagebus
fi

%postun
/sbin/ldconfig
if [ "$1" -ge "1" ]; then
  service messagebus condrestart > /dev/null 2>&1
fi

%files
%defattr(-,root,root)

%doc COPYING ChangeLog NEWS

%dir %{_sysconfdir}/dbus-1
%config %{_sysconfdir}/dbus-1/*.conf
%config %{_sysconfdir}/rc.d/init.d/*
%dir %{_sysconfdir}/dbus-1/system.d
%dir %{_localstatedir}/run/dbus
%dir %{_libdir}/dbus-1.0
%{_bindir}/dbus-daemon-1
%{_bindir}/dbus-send
%{_bindir}/dbus-cleanup-sockets
%{_libdir}/*dbus-1*.so.*
%{_datadir}/man/man*/*
%{_datadir}/dbus-1/services

%files devel
%defattr(-,root,root)

%{_libdir}/lib*.a
%{_libdir}/lib*.so
%{_libdir}/dbus-1.0/include
%{_libdir}/pkgconfig/*
%{_includedir}/*

%files glib
%defattr(-,root,root)

%{_libdir}/*glib*.so.*
%{_bindir}/dbus-glib-tool
%{_bindir}/dbus-monitor

%if 0
%files gtk
%defattr(-,root,root)

%{_bindir}/dbus-viewer

%endif

%if 0
%files qt
%defattr(-,root,root)

%{_libdir}/*qt*.so.*

%endif

%files x11
%defattr(-,root,root)

%{_bindir}/dbus-launch

%files python
%defattr(-,root,root)
%{_libdir}/python*/site-packages/dbus.py
%{_libdir}/python*/site-packages/dbus.pyc
%{_libdir}/python*/site-packages/dbus.pyo
%{_libdir}/python*/site-packages/dbus_bindings.a
%{_libdir}/python*/site-packages/dbus_bindings.la
%{_libdir}/python*/site-packages/dbus_bindings.so

%changelog
* Wed Sep 22 2004 John (J5) Palmieri <johnp@redhat.com>
- Fixed patch to use dbus-1 instead of dbus-1.0
- (configure.in): Exported just the datadir instead of
  the full path to the dbus datadir for consistency

* Wed Sep 22 2004 John (J5) Palmieri <johnp@redhat.com>
- Adding patch to move /usr/lib/dbus-1.0/services to
  /usr/share/dbus-1.0/services 

* Thu Sep 16 2004 John (J5) Palmieri <johnp@redhat.com>
- reverting BuildRequires: redhat-release because of issues with build system
- added precompiled version of the messagebus init script

* Thu Sep 16 2004 John (J5) Palmieri <johnp@redhat.com>
- changed /etc/redhat-release to the package redhat-release

* Thu Sep 16 2004 John (J5) Palmieri <johnp@redhat.com>
- added python int64 patch from davidz

* Thu Sep 16 2004 John (J5) Palmieri <johnp@redhat.com>
- added BuildRequires: /etc/redhat-release (RH Bug #132436)

* Wed Aug 18 2004 John (J5) Palmieri <johnp@redhat.com>
- Added Steve Grubb's spec file patch (RH Bug #130201)

* Mon Aug 16 2004 John (J5) Palmieri <johnp@redhat.com>
- Disabled dbus-gtk since dbus-viewer doesn't do anything right now

* Mon Aug 16 2004 John (J5) Palmieri <johnp@redhat.com>
- Moved dbus-viewer to new dbus-gtk package so that dbus-glib
  no longer requires X or GTK libraries. (RH Bug #130029)

* Thu Aug 12 2004 John (J5) Palmieri <johnp@redhat.com>
- Update to new 0.22 release

* Thu Aug 05 2004 John (J5) Palmieri <johnp@redhat.com> 
- Added BuildRequires for libselinux-devel and Requires for libselinux

* Tue Aug 02 2004 Colin Walters <walters@redhat.com>
- Add SE-DBus patch

* Fri Jul 30 2004 John (J5) Palmieri <johnp@redhat.com>
- Added lib64 workaround for python bindings installing to
  the wrong lib directory on 64 bit archs

* Fri Jul 30 2004 John (J5) Palmieri <johnp@redhat.com>
- Updated console-auth patch
- rebuild
 
* Thu Jul 22 2004 John (J5) Palmieri <johnp@redhat.com>
- Update to upstream CVS build
- Added console-auth patch

* Fri Jun 25 2004 John (J5) Palmieri <johnp@redhat.com>
- Workaround added to fix gcc-3.4 bug on ia64

* Fri Jun 25 2004 John (J5) Palmieri <johnp@redhat.com>
- require new Pyrex version and see if it builds this time

* Fri Jun 25 2004 John (J5) Palmieri <johnp@redhat.com>
- rebuild with updated Pyrex (0.9.2.1)

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Fri Jun 04 2004 John (J5) Palmieri <johnp@redhat.com>
- Moved dbus-viewer, dbus-monitor and dbus-glib-tool 
  into the dbus-glib package so that the main dbus
  package does not depend on glib (Bug #125285) 

* Thu Jun 03 2004 John (J5) Palmieri <johnp@redhat.com>
- rebuilt

* Thu May 27 2004 John (J5) Palmieri <johnp@redhat.com>
- added my Python patch
- took out the qt build requires
- added a gtk+ build requires 

* Fri Apr 23 2004 John (J5) Palmieri <johnp@redhat.com>
- Changed build requirement to version 0.9-3 of Pyrex
  to fix problem with builing on x86_64

* Tue Apr 20 2004 John (J5) Palmieri <johnp@redhat.com>
- update to upstream 0.21
- removed dbus-0.20-varargs.patch patch (fixed upstream)

* Mon Apr 19 2004 John (J5) Palmieri <johnp@redhat.com>
- added a dbus-python package to generate python bindings
- added Pyrex build dependacy

* Tue Mar 02 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Wed Feb 25 2004 Bill Nottingham <notting@redhat.com> 0.20-4
- fix dbus error functions on x86-64 (#116324)
- add prereq (#112027)

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Fri Feb 13 2004 Tim Waugh <twaugh@redhat.com>
- Conflict with cups prior to configuration file change, so that the
  %%postun service condrestart works.

* Wed Feb 11 2004 Havoc Pennington <hp@redhat.com> 0.20-2
- rebuild in fc2, cups now updated

* Wed Jan  7 2004 Bill Nottingham <notting@redhat.com> 0.20-1
- update to upstream 0.20

* Thu Oct 16 2003 Havoc Pennington <hp@redhat.com> 0.13-6
- hmm, dbus doesn't support uids in the config file. fix.

* Thu Oct 16 2003 Havoc Pennington <hp@redhat.com> 0.13-5
- put uid instead of username in the config file, to keep things working with name change

* Thu Oct 16 2003 Havoc Pennington <hp@redhat.com> 0.13-4
- make subpackages require the specific release, not just version, of base package

* Thu Oct 16 2003 Havoc Pennington <hp@redhat.com> 0.13-3
- change system user "messagebus" -> "dbus" to be under 8 chars

* Mon Sep 29 2003 Havoc Pennington <hp@redhat.com> 0.13-2
- see if removing qt subpackage for now will get us through the build system,
  qt bindings not useful yet anyway

* Sun Sep 28 2003 Havoc Pennington <hp@redhat.com> 0.13-1
- 0.13 fixes a little security oops

* Mon Aug  4 2003 Havoc Pennington <hp@redhat.com> 0.11.91-3
- break the tiny dbus-launch that depends on X into separate package
  so a CUPS server doesn't need X installed

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Sat May 17 2003 Havoc Pennington <hp@redhat.com> 0.11.91-1
- 0.11.91 cvs snap properly merges system.d

* Fri May 16 2003 Havoc Pennington <hp@redhat.com> 0.11.90-1
- build a cvs snap with a few more fixes

* Fri May 16 2003 Havoc Pennington <hp@redhat.com> 0.11-2
- fix a crash that was breaking cups

* Thu May 15 2003 Havoc Pennington <hp@redhat.com> 0.11-1
- 0.11

* Thu May 15 2003 Havoc Pennington <hp@redhat.com> 0.10.90-1
- use rc.d/init.d not init.d, bug #90192
- include the new man pages

* Fri Apr 11 2003 Havoc Pennington <hp@redhat.com> 0.9-1
- 0.9
- export QTDIR explicitly
- re-enable qt, the problem was most likely D-BUS configure

* Tue Apr  1 2003 Havoc Pennington <hp@redhat.com> 0.6.94-1
- update from CVS with a fix to set uid after gid

* Tue Apr  1 2003 Havoc Pennington <hp@redhat.com> 0.6.93-1
- new cvs snap that actually forks to background and changes 
  user it's running as and so forth
- create our system user in pre

* Mon Mar 31 2003 Havoc Pennington <hp@redhat.com> 0.6.92-1
- fix for "make check" test that required a home directory

* Mon Mar 31 2003 Havoc Pennington <hp@redhat.com> 0.6.91-1
- disable qt for now because beehive hates me
- pull a slightly newer cvs snap that creates socket directory
- cat the make check log after make check fails

* Mon Mar 31 2003 Havoc Pennington <hp@redhat.com> 0.6.90-1
- initial build

