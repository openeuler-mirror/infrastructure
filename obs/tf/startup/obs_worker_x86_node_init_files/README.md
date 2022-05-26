# note

> X86节点进行初始化，按照如下步骤进行: 适用于 `openEuler 20.03 64bit` 操作系统

* 创建目录

  ```shell
  mkdir /obs && mv ./{cpuNum,init.sh,obs_worker_openeuler_x86.sh,worker_ip_add} /obs
  cd /obs
  ```

* 赋予文件执行权限

  ```shell
  chmod a+x ./init.sh
  chmod a+x ./obs_worker_openeuler_x86.sh
  ```

* 设置重启方式初始化

  ```shell
  STR="@reboot /obs/init.sh"
  ( echo "$STR" ) | crontab -
  ```

* 说明

  1. 可以使用两种方式初始化：
    第一种方式：直接执行`./obs_worker_openeuler_x86.sh`就可以完成初始化；适合于单个节点执行；
    完成初始化后，`cpuNum`中的值为`cpu`物理个数时，初始化正常；

  2. 第二种方式：重启后自动完成初始化，初始化后，检查`cpuNum`中的值为`cpu`物理个数时，初始化正常；适合于远程批量执行；

  3. 如有异常，请检查日志文件:`/var/log/install_obs_worker.log`.