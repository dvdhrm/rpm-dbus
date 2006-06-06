%define pyver %(python -c 'import sys ; print sys.version[:3]')
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_pytho\n_lib()")}

%define gettext_package dbus

%define expat_version           1.95.5
%define glib2_version           2.2.0
%define qt_basever		3.3
%define qt_version              3.3.0
%define pyrex_version		0.9.3
%define gtk2_version		2.4.0
%define libselinux_version	1.15.2	

%define dbus_user_uid           81

# Mono only availible on these:
%define mono_archs %ix86 x86_64 ppc ia64 armv4l sparc s390 s390x

Summary: D-BUS message bus
Name: dbus
Version: 0.61
Release: 6
URL: http://www.freedesktop.org/software/dbus/
Source0: %{name}-%{version}.tar.gz
License: AFL/GPL
Group: System Environment/Libraries
BuildRoot: %{_tmppath}/%{name}-root
PreReq: /usr/sbin/useradd
Requires: chkconfig >= 1.3.26
BuildPreReq: libtool
#BuildRequires: redhat-release 
BuildRequires: expat-devel >= %{expat_version}
BuildRequires: libxml2-devel
BuildRequires: glib2-devel >= %{glib2_version}
#BuildRequires: qt-devel    >= %{qt_version}
BuildRequires: Pyrex	   >= %{pyrex_version}
#BuildRequires: gtk2-devel  >= %{gtk_version}
BuildRequires: libselinux-devel >= %{libselinux_version}
BuildRequires: audit-libs-devel >= 0.9
BuildRequires: libX11-devel
BuildRequires: libICE-devel
BuildRequires: libSM-devel
BuildRequires: libcap-devel
%ifarch %mono_archs
BuildRequires: mono-devel gtk-sharp
%endif

Requires: libselinux >= %{libselinux_version}

Conflicts: cups < 1:1.1.20-4

Patch1: dbus-0.32-selinux_chroot_workaround.patch
Patch2: dbus-0.61-selinux-avc-audit.patch
Patch3: dbus-0.60-start-early.patch
#make sure we take this out if ABI changes
Patch4: dbus-0.61-mono-no-abi-version-change.patch 

Patch5: dbus-0.61.dbus-connection.c.backport.patch

%description

D-BUS is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.

%package devel
Summary: Libraries and headers for D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}
Requires: glib2-devel 

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
Requires: libX11
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

%ifarch %mono_archs
%package sharp
Summary: mono bindings for D-BUS
Group: Development/Libraries
Requires: %name = %{version}-%{release}

%description sharp
D-BUS mono bindings for use with mono programs.   
%endif

%prep
%setup -q

%patch1 -p1 -b .selinux_chroot_workaround
%patch2 -p1 -b .selinux-avc-audit
%patch3 -p1 -b .start-early

#make sure we take this out if ABI changes
%patch4 -p1 -b .mono-no-abi-version-change

%patch5 -p1 -b .backport

autoreconf -f -i

%build
%ifarch %mono_archs
export MONO_SHARED_DIR=%{_builddir}/%{?buildsubdir}
MONO_ARGS="--enable-mono"
%endif
COMMON_ARGS="--enable-glib=yes --enable-libaudit --enable-selinux=yes --disable-gtk --disable-qt --disable-qt3 --with-init-scripts=redhat --with-system-pid-file=%{_localstatedir}/run/messagebus.pid --with-dbus-user=%{dbus_user_uid} $MONO_ARGS"

if test -d %{_libdir}/qt-%{qt_basever} ; then
   export QTDIR=%{_libdir}/qt-%{qt_basever}
else
   echo "WARNING: %{_libdir}/qt-%{qtbasever} does not exist"
fi

### this is some crack because bits of dbus can be 
### smp-compiled but others don't feel like working
function make_fast() {
        ### try to burn through it with SMP a couple times
        make %{?_smp_mflags} || true
        make %{?_smp_mflags} || true

        ### then do a real make and don't ignore failure
        DBUS_VERBOSE=1 make
}

#%ifarch ia64
#FIXME: workaround for gcc-3.4 bug which causes python bindings build to hand on ia64 arches
#CFLAGS="$RPM_OPT_FLAGS -O1"
#export CFLAGS
#%endif

#### Build once with tests to make check
%configure $COMMON_ARGS --enable-tests=yes --enable-verbose-mode=yes --enable-asserts=yes
make_fast
exit 0
DBUS_VERBOSE=1 make check > dbus-check.log 2>&1 || (cat dbus-check.log && false)

#### Clean up and build again 
make clean 

%configure $COMMON_ARGS --disable-tests --disable-verbose-mode --disable-asserts
make

%install
rm -rf %{buildroot}
export MONO_SHARED_DIR=%{_builddir}/%{?buildsubdir}

# dbus installs mono files in libdir, not in prefix/lib, fixup:
perl -pi -e 's,/gacdir \$\(libdir\),/gacdir /usr/lib,g' mono/Makefile
perl -pi -e "s,/root \\\$\\(DESTDIR\\)\\\$\(libdir\\),/root $RPM_BUILD_ROOT/usr/lib,g" mono/Makefile
perl -pi -e "s,/usr/lib64,/usr/lib,g" dbus-sharp.pc
mkdir -p $RPM_BUILD_ROOT%{_prefix}/lib/mono

make install DESTDIR=$RPM_BUILD_ROOT

rm -f $RPM_BUILD_ROOT%{_libdir}/*.a

rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

rm -f $RPM_BUILD_ROOT%{_libdir}/python*/site-packages/dbus/*.*a

# move the base dbus libraries and executables to /bin and /lib
mkdir -p $RPM_BUILD_ROOT/bin
mkdir -p $RPM_BUILD_ROOT/%{_lib}

mv -f $RPM_BUILD_ROOT%{_libdir}/*dbus-1*.so.* $RPM_BUILD_ROOT/%{_lib}
mv -f $RPM_BUILD_ROOT%{_bindir}/dbus-daemon $RPM_BUILD_ROOT/bin
mv -f $RPM_BUILD_ROOT%{_bindir}/dbus-send $RPM_BUILD_ROOT/bin
mv -f $RPM_BUILD_ROOT%{_bindir}/dbus-cleanup-sockets $RPM_BUILD_ROOT/bin

# Create a dummy file so that no matter how deep we are we can
# find the root directory.
touch $RPM_BUILD_ROOT/rootfile

# We need to make relative links to dbus-send
# Search for the file relative to the location of %%{_bindir}.
root=..
while [ ! -e $RPM_BUILD_ROOT/%{_bindir}/${root}/rootfile ] ; do
        root=${root}/..
done

# Actually create the link.
pushd $RPM_BUILD_ROOT/%{_bindir}
ln -f -s ${root}/bin/dbus-send dbus-send
popd
	

# We need to make relative links to the moved libaries
# Search for the file relative to the location of %%{_libdir}.
root=..
while [ ! -e $RPM_BUILD_ROOT/%{_libdir}/${root}/rootfile ] ; do
        root=${root}/..
done

# Actually create the link.
pushd $RPM_BUILD_ROOT/%{_libdir}
for so_file in *dbus-1*.so ; do 
	ln -f -s ${root}/%{_lib}/$so_file.? $so_file
done
popd
# Clean it up.
rm $RPM_BUILD_ROOT/rootfile

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
/sbin/chkconfig messagebus resetpriorities

%preun
if [ $1 = 0 ]; then
    /sbin/chkconfig --del messagebus
fi

%postun
/sbin/ldconfig

%post glib -p /sbin/ldconfig
%postun glib -p /sbin/ldconfig

%files
%defattr(-,root,root)

%doc COPYING ChangeLog NEWS

%dir %{_sysconfdir}/dbus-1
%config %{_sysconfdir}/dbus-1/*.conf
%config %{_sysconfdir}/rc.d/init.d/*
%dir %{_sysconfdir}/dbus-1/system.d
%dir %{_localstatedir}/run/dbus
%dir %{_libdir}/dbus-1.0
/bin/dbus-daemon
/bin/dbus-send
%{_bindir}/dbus-send
/bin/dbus-cleanup-sockets
/%{_lib}/*dbus-1*.so.*
%{_datadir}/man/man*/*
%{_datadir}/dbus-1/services

%files devel
%defattr(-,root,root)

%{_libdir}/lib*.so
%{_libdir}/dbus-1.0/include
%{_libdir}/pkgconfig/dbus-1.pc
%{_libdir}/pkgconfig/dbus-glib-1.pc
%{_includedir}/*

%files glib
%defattr(-,root,root)

%{_libdir}/*glib*.so.*
%{_bindir}/dbus-binding-tool
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
%{_libdir}/python*/site-packages/dbus/*.so
%{_libdir}/python*/site-packages/dbus.pth
%{_libdir}/python*/site-packages/dbus/*.py*

%ifarch %mono_archs
%files sharp
%defattr(-,root,root)
%{_prefix}/lib/mono/dbus-sharp
%{_prefix}/lib/mono/gac/dbus-sharp
%{_libdir}/pkgconfig/dbus-sharp.pc
%endif

%changelog
* Tue Jun  6 2006 Matthias Clasen <mclasen@redhat.com> 0.61-6
- Rebuild

* Wed May 17 2006 Karsten Hopp <karsten@redhat.de> 0.61-5.2 
- add buildrequires libICE-devel, libSM-devel, libcap-devel
- change buildrequires form libX11 to libX11-devel

* Mon May 15 2006 John (J5) Palmieri <johnp@redhat.com> - 0.61-5.1
- Bump and rebuild.  Add a BR and R for libX11

* Tue Apr 25 2006 John (J5) Palmieri <johnp@redhat.com> - 0.61-5
- Backport patch from dbus-connection.c
  - Allows interfaces to be NULL in the message header as per the spec
  - Fixes a problem with pendings calls blocking on a data starved socket

* Mon Apr 17 2006 John (J5) Palmieri <johnp@redhat.com> 0.61-4
- New audit patch

* Fri Feb 24 2006 John (J5) Palmieri <johnp@redhat.com> 0.61-3
- ABI hasn't changed so add patch that makes dbus-sharp think
  it is still 0.60 (mono uses hard version names so any change
  means apps need to recompile)

* Fri Feb 24 2006 John (J5) Palmieri <johnp@redhat.com> 0.61-2
- Make sure chkconfig rests the priorities so we can start earlier

* Fri Feb 24 2006 John (J5) Palmieri <johnp@redhat.com> 0.61-1
- Upgrade to upstream version 0.61
- remove python callchain patch
- update avc patch

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 0.60-7.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 0.60-7.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Mon Jan 23 2006 John (J5) Palmieri <johnp@redhat.com> 0.60-7
- Add patch to fix the python callchain
- Symlink dbus-send to /usr/bin because some applications
  look for it there

* Fri Jan 20 2006 John (J5) Palmieri <johnp@redhat.com> 0.60-6
- Fix up patch to init script so it refrences /bin not /usr/bin

* Fri Jan 20 2006 John (J5) Palmieri <johnp@redhat.com> 0.60-5
- move base libraries and binaries to /bin and /lib so they can be started
  before /usr is mounted on network mounted /usr systems
- have D-Bus start early

* Thu Jan 19 2006 Alexander Larsson <alexl@redhat.com> 0.60-4
- mono now built on s390x

* Mon Jan  9 2006 Alexander Larsson <alexl@redhat.com> 0.60-3
- Don't exclude non-mono arches

* Mon Jan  9 2006 Alexander Larsson <alexl@redhat.com> - 0.60-2
- Add dbus-sharp sub-package

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com> - 0.60-1.1
- rebuilt

* Thu Dec 01 2005 John (J5) Palmieri <johnp@redhat.com> - 0.60-1
- upgrade to 0.60

* Mon Sep 08 2005 John (J5) Palmieri <johnp@redhat.com> - 0.50-1
- upgrade to 0.50

* Mon Aug 29 2005 John (J5) Palmieri <johnp@redhat.com> - 0.36.2-1
- upgrade to 0.36.2 which fixes an exploit where
  users can attach to another user's session bus (CAN-2005-0201)

* Wed Aug 24 2005 John (J5) Palmieri <johnp@redhat.com> - 0.36.1-1
- Upgrade to dbus-0.36.1
- Install all files to lib64/ on 64bit machines

* Tue Aug 23 2005 John (J5) Palmieri <johnp@redhat.com> - 0.36-1
- Upgrade to dbus-0.36
- Split modules that go into %{_lib}/python2.4/site-packages/dbus
and those that go into %{python_sitelib}/dbus (they differ on 64bit)
- Renable Qt bindings since packages in core can use them

* Mon Jul 18 2005 John (J5) Palmieri <johnp@redhat.com> - 0.35.2-1
- Upgrade to dbus-0.35.2
- removed dbus-0.34-kill-babysitter.patch
- removed dbus-0.34-python-threadsync.patch
- removed dbus-0.23-selinux-avc-audit.patch
- added dbus-0.35.2-selinux-avc-audit.patch
- take out restarts on upgrade

* Tue Jun 28 2005 John (J5) Palmieri <johnp@redhat.com> - 0.34-1
- Upgrade to dbus-0.34
- added dbus-0.34-kill-babysitter.patch
- added dbus-0.34-python-threadsync.patch
- remove dbus-0.32-print_child_pid.patch
- remove dbus-0.32-deadlock-fix.patch
- remove dbus-0.33-types.patch

* Wed Jun 18 2005 John (J5) Palmieri <johnp@redhat.com> - 0.33-4
- Add new libaudit patch from Steve Grub and enable in configure
  (Bug #159218)

* Mon May 23 2005 Bill Nottingham <notting@redhat.com> - 0.33-3
- remove static libraries from python bindings

* Sun May 01 2005 John (J5) Palmieri <johnp@redhat.com> - 0.33-2
- Backport patch from CVS that fixes int32's being marshaled as
uint16's in the python bindings

* Mon Apr 25 2005 John (J5) Palmieri <johnp@redhat.com> - 0.33-1
- update to upstream 0.33
- renable selinux audit patch

* Mon Apr 12 2005 John (J5) Palmieri <johnp@redhat.com> - 0.32-6
- Added patch to fix deadlocks when using recursive g_mains

* Mon Apr 12 2005 John (J5) Palmieri <johnp@redhat.com> - 0.32-5
- replace selinux_init patch with selinux_chroot_workaround patch
  to work around bad selinux interactions when using chroots
  on the beehive build machines

* Mon Apr 11 2005 John (J5) Palmieri <johnp@redhat.com> - 0.32-4
- add print_child_pid patch which make sure we prin the child's pid if we fork

* Thu Apr  7 2005 David Zeuthen <davidz@redhat.com> - 0.32-3
- add fix for glib infinite loop (fdo #2889)

* Thu Mar 31 2005 John (J5) Palmieri <johnp@redhat.com> - 0.32-2
- add selinux-init patch to fix dbus from segfaulting when
  building on machines that don't have selinux enabled

* Thu Mar 31 2005 John (J5) Palmieri <johnp@redhat.com> - 0.32-1
- update to upstream version 0.32

* Wed Mar 23 2005 John (J5) Palmieri <johnp@redhat.com> - 0.31-4
- Pyrex has been patched to generate gcc4.0 complient code
- Rebuild for gcc4.0
 
* Wed Mar 16 2005 John (J5) Palmieri <johnp@redhat.com> - 0.31-3
- change compat-gcc requirement to compat-gcc-32
- rebuild with gcc 3.2

* Tue Mar 08 2005 John (J5) Palmieri <johnp@redhat.com> - 0.31-2
- Remove precompiled init script and let the sources generate it

* Mon Mar 07 2005 John (J5) Palmieri <johnp@redhat.com> - 0.31-1
- update to upstream version 0.31
- take out user has same id patch (merged upstream)
- udi patch updated
- dbus-daemon-1 renamed to dbus-daemon
- dbus-glib-tool renamed to dbus-binding-tool
- force gcc33 because pyrex generate improper lvalue code
- disable audit patch for now

* Tue Feb 01 2005 John (J5) Palmieri <johnp@redhat.com> - 0.23-4
- Explicitly pass in the pid file location to ./configure instead of
  letting it guess based on the build enviornment

* Mon Jan 31 2005 John (J5) Palmieri <johnp@redhat.com> - 0.23-3
- Add patch to fix random users from connecting to a users session bus

* Fri Jan 21 2005 John (J5) Palmieri <johnp@redhat.com> - 0.23-2
- Add Steve Grubb's SE-Linux audit patch (Bug# 144920)

* Fri Jan 21 2005 John (J5) Palmieri <johnp@redhat.com> - 0.23-1
- Update to upstream version 0.23
- Drop all patches except for the UDI patch as they have been 
  integrated upstream 
- List of API changes:
      * add setgroups() to drop supplementary groups
      * removed dbus_bug_get_with_g_main since it's been replaced by dbus_g_bus_get
      * added support for int64 and uint64 to the python bindings
      * use SerivceOwnerChanges signal instead of ServiceCreated and ServiceDeleted

* Mon Nov  8 2004 Jeremy Katz <katzj@redhat.com> - 0.22-12
- rebuild against python 2.4

* Tue Nov 02 2004 John (J5) Palmieri <johnp@redhat.com>
- Add a requires for glib2-devel in the devel package
- Add SE-Linux backport from Colin Walters that fixes 
  messages getting lost in SE-Linux contexts

* Wed Oct 13 2004 John (J5) Palmieri <johnp@redhat.com>
- Bump up release and rebuild

* Mon Oct 11 2004 Tim Waugh <twaugh@redhat.com>
- Run /sbin/ldconfig for glib sub-package (bug #134062).

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

