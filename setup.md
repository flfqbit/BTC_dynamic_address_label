# 代码部署、测试相关操作
###### 高峰20200322

## 1 代码部署流程

1.  安装`python3.7.6`

2.  安装`pycharm`

3.  下载代码(`github`)，并用`pycharm`打开项目

4.  配置`pycharm`

    *   快捷键：`ctr+alt+s`；打开`settings`
    *   选中`settings/Projec:BCC_site/Project Interpreter`,在`Project Interpreter`栏中，建立一个`Pyhton 3.7(BCC_site)`的库。
    *   建库方法，选中下拉框的`Show ALL`进入`Project Interpreters`,点击右侧的`+`号;
    *   `Location`栏填入库位置，注意，位置信息是一个空文件夹的目录，文件夹名称必须是`BCC_site`;
    *   `Base Interpreter`栏，填入`python3.7`的安装目录，指向`xx/python.exe`

5.  更新库

    *   根据项目中文档`requirements.txt`中的数据，安装所需外部库

    *   两种方法：

        1.  `pip install -r requirements.txt`

        2.  利用`pycharm`自带的安装库功能自动安装（`IDE`默认会弹出提示框）

6.  输入指令，验证是否完成
    *   `py user_operation_test.py`
    *   `py manage.py runserver`

## 2 其他配置信息


比特币测试链浏览器：
- 比特币测试链浏览器 https://live.blockcypher.com/btc-testnet/
- 比特币测试链浏览器 https://tbtc.bitaps.com/

比特币`API`所需的`token`获取网址
- https://accounts.blockcypher.com/

比特币测试链-代币获取网址
- https://coinfaucet.eu/en/btc-testnet/
- https://testnet.help/en/btcfaucet/testnet/
- https://testnet-faucet.mempool.co/

以太坊测试链浏览器：
- 以太坊测试链浏览器：https://rinkeby.etherscan.io/

以太坊测试链-代币获取网址：
- Faucet：https://faucet.metamask.io/ 

## 3 服务器运行部署流程

1.  以`wankaibin`用户登陆，进入到`~\BCC_site`内，进入后会自动激活`Python`虚拟环境
2.  如果仓库有更新，需要先运行`git pull`将新的更新拉到本地合并
3.  运行`./start.sh`启动网站后台，默认端口是`5013`，进程默认启动为**守护进程**
    *   或者如果只是短暂启动，不需要长期驻留后台，可以使用`python manage.py runserver 0.0.0.0:5013`启动网站，但是`ssh`断开连接后，进程会被杀
4.  通过`3.`方法启动的后台，如果需要退出，执行下述操作
    *   `ps aux | grep python`
    *   找到列出的进程中，运行的`python`后台进程（一般有两个），记录下端口`port_number`
    *   `kill port_number`



#### Trouble shooting

1.  启动时报错，`ImportError: No module named django`或其它

    *   可能没有激活虚拟环境，进入到`~/BCC_site`内，重新运行

    *   缺少必要的文件夹`logs`，在`~/BCC_site`文件夹下创建新的文件夹`logs`
    *   可能没有以`wankaibin`的身份登陆，脚本有权限问题，切换到`wankaibin`用户
    *   端口被占用，可能现在有程序占用了`5013`端口，换一个端口启动试试

2.  启动成功，但是无法从浏览器访问

    *   可能刚启动，云服务器接入请求要一定时间，过十几秒刷新一次看看
    *   服务器安全组端口`5013`或其它使用的端口没有放通
    *   项目配置`settings`有问题
        *   进入到`~/BCC_site/BCC_site`下，打开`vim settings.py`
        *   找到`DEBUG`和`ALLOWED_HOST`这两行，一般在一起
        *   设置为`DEBUG=False`和`ALLOWED_HOSTS = ['*']`
        *   重新启动脚本

3.  运行中报错

    *   一般是网络连接问题，这台`vps`虽然是连通外网的，但是偶尔还是会超时，重试几次。