#!/bin/bash
# Provide missing FastCDR 2.x symbols.
#
# FastCDR 2.2.5 (shipped with ROS2 Jazzy) dropped several Cdr::serialize()
# overloads that used to exist in 1.x.  The pre-built
# *__rosidl_typesupport_fastrtps*.so libraries still reference the old symbols,
# so gz-sim-server crashes at startup with "undefined symbol" errors.
#
# The shim forwards each missing overload to its binary-compatible replacement:
#   serialize(unsigned int)         → serialize(int)        [same 4-byte layout]
#   serialize(unsigned long)        → serialize(long)       [same 8-byte layout]
#   serialize(unsigned short)       → serialize(short)      [same 2-byte layout]
#   serialize(signed char)          → serialize(char)       [same 1-byte layout]
#   serialize(const unsigned char&) → serialize(char)       [same 1-byte layout]
#   serialize(char*)                → serialize(const char*)[non-const → const]
if command -v gcc >/dev/null 2>&1; then
    cat > /tmp/fastcdr_shim.c << 'EOF'
/*
 * FastCDR 2.x compatibility shim
 * Maps old Cdr::serialize overloads to their binary-equivalent replacements.
 * All forwarded types share the same in-memory representation on every
 * architecture ROS2 supports (x86_64, aarch64, armv7).
 */

/* Declarations of the symbols that DO exist in libfastcdr.so.2.2.5 */
extern void _ZN8eprosima7fastcdr3Cdr9serializeEi(void*, int);           /* int           */
extern void _ZN8eprosima7fastcdr3Cdr9serializeEl(void*, long);          /* long          */
extern void _ZN8eprosima7fastcdr3Cdr9serializeEs(void*, short);         /* short         */
extern void _ZN8eprosima7fastcdr3Cdr9serializeEc(void*, char);          /* char          */
extern void _ZN8eprosima7fastcdr3Cdr9serializeEPKc(void*, const char*); /* const char*   */

/* serialize(unsigned int) — 'j' */
void _ZN8eprosima7fastcdr3Cdr9serializeEj(void* cdr, unsigned int v)
    { _ZN8eprosima7fastcdr3Cdr9serializeEi(cdr, (int)v); }

/* serialize(unsigned long) — 'm' */
void _ZN8eprosima7fastcdr3Cdr9serializeEm(void* cdr, unsigned long v)
    { _ZN8eprosima7fastcdr3Cdr9serializeEl(cdr, (long)v); }

/* serialize(unsigned short) — 't' */
void _ZN8eprosima7fastcdr3Cdr9serializeEt(void* cdr, unsigned short v)
    { _ZN8eprosima7fastcdr3Cdr9serializeEs(cdr, (short)v); }

/* serialize(signed char) — 'a' */
void _ZN8eprosima7fastcdr3Cdr9serializeEa(void* cdr, signed char v)
    { _ZN8eprosima7fastcdr3Cdr9serializeEc(cdr, (char)v); }

/* serialize(const unsigned char&) — 'RKh'
   The & means a pointer to unsigned char is passed; cast to char*. */
void _ZN8eprosima7fastcdr3Cdr9serializeERKh(void* cdr, const unsigned char* v)
    { _ZN8eprosima7fastcdr3Cdr9serializeEc(cdr, (char)*v); }

/* serialize(char*) — 'Pc'  (non-const string, same as const) */
void _ZN8eprosima7fastcdr3Cdr9serializeEPc(void* cdr, char* v)
    { _ZN8eprosima7fastcdr3Cdr9serializeEPKc(cdr, (const char*)v); }
EOF
    if gcc -shared -fPIC -o /tmp/libfastcdr_shim.so /tmp/fastcdr_shim.c \
            -L/opt/ros/jazzy/lib -lfastcdr 2>/dev/null; then
        export LD_PRELOAD=/tmp/libfastcdr_shim.so
        echo "[entrypoint] FastCDR compatibility shim loaded (6 symbols)."
    else
        echo "[entrypoint] WARNING: shim compile failed — Gazebo may crash on startup."
    fi
else
    echo "[entrypoint] WARNING: gcc not found — FastCDR shim skipped."
fi

# Remove stale coverage_planner ament index entry that points to a plugins.xml
# which doesn't exist yet (plugin not built), causing pluginlib to spam errors.
rm -f /opt/ws/install/open_mower_next/share/ament_index/resource_index/nav2_core__pluginlib__plugin/open_mower_next

python3 -m pip install pyserial transforms3d --break-system-packages 2>/dev/null || true

source /opt/ros/jazzy/setup.bash
source install/setup.bash
exec ros2 launch open_mower_next sim.launch.py